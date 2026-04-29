import csv
from pathlib import Path

import numpy as np
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, Button, DataTable, Select
from textual.binding import Binding
from textual.widgets._directory_tree import DirectoryTree
from textual_plotext import PlotextPlot as tpp


def read_csv_headers(csv_path: str) -> list[str]:
    path = Path(csv_path)

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        sample = csv_file.read(4096)
        csv_file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(csv_file, dialect)
        headers = next(reader, None)

    return list(headers or [])


def read_csv_columns(csv_path: str, x_name: str, y_name: str) -> tuple[list[float], list[float]]:
    x_values: list[float] = []
    y_values: list[float] = []
    path = Path(csv_path)

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        sample = csv_file.read(4096)
        csv_file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(csv_file, dialect=dialect)

        for row in reader:
            try:
                x_value = float(row[x_name])
                y_value = float(row[y_name])
            except (KeyError, TypeError, ValueError):
                continue

            x_values.append(x_value)
            y_values.append(y_value)

    return x_values, y_values


class FilePickerScreen(ModalScreen[str | None]):
    CSS = """
    FilePickerScreen {
        align: center middle;
    }

    #picker-dialog {
        width: 80%;
        height: 80%;
        padding: 1 2;
        border: round #89b4fa;
        background: #313244;
    }

    #picker-title {
        height: 3;
        content-align: center middle;
        color: #f9e2af;
        text-style: bold;
    }

    #picker-hint {
        height: 1;
        content-align: center middle;
        color: #a6e3a1;
        margin-bottom: 1;
    }

    #picker-tree {
        height: 1fr;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container(id="picker-dialog"):
            yield Static("Choose a file", id="picker-title")
            yield Static("Enter on a file to select it, Esc to cancel", id="picker-hint")
            yield DirectoryTree(Path.cwd(), id="picker-tree")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(str(event.path))

    def action_cancel(self) -> None:
        self.dismiss(None)



class CsvInspectorScreen(ModalScreen[None]):
    #Csv fil inspector med konfigurerbart antal viste rækker
    
    CSS = """
    CsvInspectorScreen {
        align: center middle;
    }

    #inspector-dialog {
        width: 95%;
        height: 90%;
        padding: 1 2;
        border: round #89b4fa;
        background: #313244;
        layout: vertical;
    }

    #inspector-header {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
    }

    #inspector-title {
        width: 1fr;
        color: #f9e2af;
        text-style: bold;
    }

    #inspector-stats {
        width: auto;
        color: #a6e3a1;
        text-align: right;
    }

    #inspector-controls {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
    }

    #row-count-select {
        width: 15;
    }

    #row-count-control {
        width: auto;
        margin-right: 2;
    }

    #inspector-table {
        height: 1fr;
        margin-bottom: 1;
    }

    #inspector-footer {
        height: auto;
        layout: horizontal;
        content-align: center middle;
    }

    #inspector-footer Button {
        width: 18;
        margin: 0 1;
    }
    """

    BINDINGS = [Binding("escape", "close", "Close")]        #luk vinduet med esc

    def __init__(self, csv_path: str) -> None:      #Initialiserer klassen med csv filens path og forbereder variabler
        super().__init__()
        self.csv_path = csv_path
        self.all_rows: list[list[str]] = []
        self.headers: list[str] = []
        self.max_rows = 10
        self.total_rows = 0

    def compose(self) -> ComposeResult:         # Definerer layoutet for knapperne og datacellerne i CSV-inspectoren
        with Container(id="inspector-dialog"):
            # Header med filnavn og statistik
            with Container(id="inspector-header"):
                yield Static(f"CSV Inspector: {Path(self.csv_path).name}", id="inspector-title")
                yield Static("", id="inspector-stats")

                    
            # Valg af antal rækker at vise
            with Container(id="inspector-controls"):
                yield Select(
                    [(str(n), str(n)) for n in [5, 10, 25, 50, 100]] + [("All", "All")],
                    value="10",
                    id="row-count-select",
                )
                yield Static("rows to display", id="row-count-control")

            # Data celler
            yield DataTable(id="inspector-table", show_row_labels=True)

            # Luk knap i bunden
            with Container(id="inspector-footer"):
                yield Button("Close", id="close_btn", variant="primary")

    def on_mount(self) -> None:     #Loader dataen fra CSV-filen og opdaterer tabellen
        self._load_csv_data()
        self._update_table()

    def on_select_changed(self, event: Select.Changed) -> None:     #Opdaterer tabellen når brugeren ændrer antallet af viste rækker
        
        if event.control.id == "row-count-select":
            if event.value == "All":
                self.max_rows = self.total_rows
                self._update_table()
            else:
                try:
                    self.max_rows = int(event.value)
                    self._update_table()
                except (ValueError, TypeError):
                    pass

    def _load_csv_data(self) -> None:
        #Indlæser CSV-dataen og håndterer eventuelle fejl ved filadgang
        path = Path(self.csv_path)
        
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                sample = csv_file.read(4096)
                csv_file.seek(0)
                
                dialect = _get_csv_dialect(sample)
                reader = csv.reader(csv_file, dialect=dialect)
                
                self.headers = next(reader, None) or []
                self.all_rows = list(reader)
                self.total_rows = len(self.all_rows)
        except OSError as error:
            self.headers = ["Error"]
            self.all_rows = [[str(error)]]
            self.total_rows = 1

    def _update_table(self) -> None:        #Opdaterer tabellen med de indlæste data
        
        table = self.query_one("#inspector-table", DataTable)
        table.clear(columns=True)
        
        if not self.headers:
            table.add_column("Message")
            table.add_row("CSV file is empty")
            self._update_stats()
            return
        
        # Tilføj kolonner baseret på headersne
        table.add_columns(*self.headers)
        
                
        # Tilføj rækker op til max_rows eller total_rows, alt efter hvad der er mindre
        rows_to_show = min(self.max_rows, self.total_rows)
        for i, row in enumerate(self.all_rows[:rows_to_show], start=1):
            padded_row = list(row[:len(self.headers)])
            padded_row.extend([""] * (len(self.headers) - len(padded_row)))
            
            # Pass label=str(i) to show the row number
            table.add_row(*padded_row, label=str(i))
            
        self._update_stats()

    def _update_stats(self) -> None:
        #Opdaterer statistik-teksten
        stats_widget = self.query_one("#inspector-stats", Static)
        rows_shown = min(self.max_rows, self.total_rows)
        stats_text = f"Showing {rows_shown} of {self.total_rows} rows | {len(self.headers)} columns"
        stats_widget.update(stats_text)

    

    def on_button_pressed(self, event: Button.Pressed) -> None:     #Lukker vinduet når "Close" knappen trykkes
        if event.button.id == "close_btn":
            self.dismiss()

    def action_close(self) -> None:     #Lukker vinduet når brugeren trykker på escape
        self.dismiss()


def _get_csv_dialect(sample: str) -> csv.Dialect:   
    #Forsøger at gætte CSV-dialekten baseret på et prøveudsnit af filen, og falder tilbage til standarddialekten hvis det fejler
    try:
        return csv.Sniffer().sniff(sample)
    except csv.Error:
        return csv.excel

class VariableSelectionScreen(ModalScreen[tuple[str, str] | None]):
    CSS = """
    VariableSelectionScreen { align: center middle; }
    #variables-dialog {
        width: 60; height: 32; padding: 1 2;
        border: round #89b4fa; background: #313244;
    }
    Select { margin-bottom: 1; }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, column_names: list[str]) -> None:
        super().__init__()
        self.column_names = column_names

    def compose(self) -> ComposeResult:
        col_options = [(name, name) for name in self.column_names]
        plot_options = [
            ("Scatter Plot", "scatter"),
            ("Line Plot", "line"),
            ("Bar Chart", "bar"),
            ("Histogram", "histogram"),
        ]

        with Container(id="variables-dialog"):
            yield Static("1. Select X Variable (Labels/X-Axis)")
            yield Select(col_options, prompt="X variable", id="x_select")
            
            yield Static("2. Select Y Variable (Data/Values)")
            yield Select(col_options, prompt="Y variable", id="y_select")
            
            yield Static("3. Select Plot Type")
            yield Select(plot_options, value="scatter", id="type_select", allow_blank=False)
            
            yield Button("Confirm Selection", variant="primary", id="confirm_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_btn":
            x = self.query_one("#x_select", Select).value
            y = self.query_one("#y_select", Select).value
            ptype = self.query_one("#type_select", Select).value
            
            if x and y and ptype:
                self.dismiss((x, y, ptype))

class PlotScreen(ModalScreen[None]):
    CSS = """
    PlotScreen { align: center middle; }
    #plot-container {
        width: 95%; height: 95%;
        border: round #89b4fa; background: #1e1e2e; padding: 1;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Back to Menu")]

    def __init__(self, x_data, y_data, x_label, y_label, plot_type):
        super().__init__()
        self.x_data = x_data
        self.y_data = y_data
        self.x_label = x_label
        self.y_label = y_label
        self.plot_type = plot_type

    def compose(self) -> ComposeResult:
        with Container(id="plot-container"):
            yield tpp()
            yield Static(f"Mode: {self.plot_type.upper()} | Press ESC to return", id="plot-hint")

    def on_mount(self) -> None:
            plt_widget = self.query_one(tpp)
            plt = plt_widget.plt
            plt.clear_figure()
            
            # Prepare data
            y_vals = np.array(self.y_data)
            x_vals = np.array(self.x_data)

            if self.plot_type == "scatter":
                plt.scatter(x_vals, y_vals, label="Data Points")
                plt.xlabel(self.x_label)
                plt.ylabel(self.y_label)
                
            elif self.plot_type == "line":
                # LOGIC: Average of Y per Age (X)
                # 1. Get unique ages
                unique_ages = np.unique(self.x_data)
                # 2. Calculate average of Y for each unique age
                avg_y = []
                for age in unique_ages:
                    indices = np.where(self.x_data == age)
                    avg_y.append(np.mean(np.array(self.y_data)[indices]))
                
                plt.plot(unique_ages, avg_y, color="blue", marker="dot")
                plt.xlabel(self.x_label)
                plt.ylabel(f"Average {self.y_label}")
                plt.title(f"Trend: Avg {self.y_label} by {self.x_label}")

            elif self.plot_type == "bar":
                # 1. Get unique categories from X (e.g., CP types 0, 1, 2, 3)
                categories = np.unique(x_vals)
                
                # 2. Calculate the AVERAGE of Y for each category
                # (e.g., Average Age for CP 0, Average Age for CP 1...)
                avg_y_per_category = []
                for cat in categories:
                    # Find all Y values where X matches this category
                    mask = (x_vals == cat)
                    average = np.mean(y_vals[mask])
                    avg_y_per_category.append(average)
                
                # 3. Plot as Bar
                labels = [str(int(c)) for c in categories]
                plt.bar(labels, avg_y_per_category, color="red", width=0.6)
                
                plt.xlabel(self.x_label)
                plt.ylabel(f"Average {self.y_label}")
                plt.title(f"Average {self.y_label} per {self.x_label}")

            elif self.plot_type == "histogram":
                min_val = int(np.floor(min(y_vals)))
                max_val = int(np.ceil(max(y_vals)))

                num_bins = max(1, max_val - min_val)

                counts, _ = np.histogram(y_vals, bins=num_bins)
                max_freq = int(max(counts))

                plt.hist(y_vals, bins=num_bins, color="green", label=self.y_label, width=0.5)

                x_step = 1 if num_bins <= 20 else (2 if num_bins <= 60 else 3)
                x_ticks = list(range(min_val, max_val + 1, x_step))
                plt.xticks(x_ticks)

                y_step = 1 if max_freq <= 15 else (2 if max_freq <= 45 else 3)
                plt.yticks(list(range(0, max_freq + 1, y_step)))

                plt.xlabel(self.y_label)
                plt.ylabel("Antal")


            plt.title(f"{self.plot_type.capitalize()}: {self.y_label} vs {self.x_label}")
            plt_widget.refresh()



class TUIApp(App):
    CSS = """
    Screen {
        align: center middle;
        background: #1e1e2e;
    }

    #menu-box {
        width: 50;
        height: auto;
        padding: 1 2;
        border: round #89b4fa;
        background: #313244;
    }

    #title {
        content-align: center middle;
        height: 3;
        color: #f9e2af;
        text-style: bold;
    }

    Button {
        width: 100%;
        margin: 1 0;
    }

    #status {
        margin-top: 1;
        height: 2;
        color: #a6e3a1;
        content-align: center middle;
    }
    """

    path: str | None = None
    x_name: str | None = None
    y_name: str | None = None
    x_variable: list[float] | None = None
    y_variable: list[float] | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="menu-box"):
            yield Static("MAIN MENU", id="title")
            yield Button("Load file", id="load_file")
            yield Button("Inspect data", id="inspect")
            yield Button("Set variables & Plot Type", id="set_variables")
            yield Button("Plot data", id="plot")
            yield Button("Exit", id="quit_btn")
            yield Static("Choose an option...", id="status")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "load_file":
            self.load_file()
        elif button_id == "inspect":
            self.inspect_file()
        elif button_id == "set_variables":
            self.set_variables()
        elif button_id == "plot":
            self.plot()
        elif button_id == "quit_btn":
            self.exit()

    def load_file(self):
        self.push_screen(FilePickerScreen(), self._on_file_picked)

    def _on_file_picked(self, path: str | None) -> None:
        if path is None:
            return

        self.path = path
        self.query_one("#status", Static).update(f"Selected file: {path}")

    def inspect_file(self):
        if not self.path:
            self.query_one("#status", Static).update("Load a CSV file first.")
            return

        self.push_screen(CsvInspectorScreen(self.path))
        return
    
    def set_variables(self):
        if not self.path: return
        cols = read_csv_headers(self.path)
        self.push_screen(VariableSelectionScreen(cols), self._on_variables_picked)

    def _on_variables_picked(self, selection: tuple[str, str, str] | None) -> None:
        if selection:
            self.x_name, self.y_name, self.plot_type = selection
            self.x_variable, self.y_variable = read_csv_columns(self.path, self.x_name, self.y_name)
            self.query_one("#status", Static).update(f"Type: {self.plot_type} | Y: {self.y_name}")
    
    def plot(self):
        if not self.y_variable:
            self.query_one("#status", Static).update("Select variables first!")
            return
        
        # Push the new TUI Plot Screen instead of using Matplotlib
        self.push_screen(PlotScreen(
            self.x_variable, 
            self.y_variable, 
            self.x_name, 
            self.y_name,
            self.plot_type
        ))

if __name__ == "__main__":
    TUIApp().run()