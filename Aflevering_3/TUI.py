import csv
from pathlib import Path

import matplotlib.pyplot as plt
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, Button, DataTable, Select
from textual.binding import Binding
from textual.widgets._directory_tree import DirectoryTree


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
    VariableSelectionScreen {
        align: center middle;
    }

    #variables-dialog {
        width: 80%;
        height: 70%;
        padding: 1 2;
        border: round #89b4fa;
        background: #313244;
    }

    #variables-title {
        height: 3;
        content-align: center middle;
        color: #f9e2af;
        text-style: bold;
    }

    #variables-hint {
        height: 1;
        content-align: center middle;
        color: #a6e3a1;
        margin-bottom: 1;
    }

    #variables-selects {
        height: 1fr;
        layout: vertical;
    }

    Select {
        margin-bottom: 1;
    }

    #variables-actions {
        height: 3;
        layout: horizontal;
        content-align: center middle;
    }

    #variables-actions Button {
        width: 18;
        margin: 0 1;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, column_names: list[str]) -> None:
        super().__init__()
        self.column_names = column_names

    def compose(self) -> ComposeResult:
        options = [(name, name) for name in self.column_names]

        with Container(id="variables-dialog"):
            yield Static("Choose x and y variables", id="variables-title")
            yield Static("Scroll or type to search through the columns", id="variables-hint")
            with Container(id="variables-selects"):
                yield Select(options, prompt="X variable", allow_blank=False, id="x_select")
                yield Select(options, prompt="Y variable", allow_blank=False, id="y_select")
            with Container(id="variables-actions"):
                yield Button("Cancel", id="cancel_btn")
                yield Button("Use selection", id="confirm_btn", variant="primary")

    def on_mount(self) -> None:
        x_select = self.query_one("#x_select", Select)
        y_select = self.query_one("#y_select", Select)

        if self.column_names:
            x_select.value = self.column_names[0]
            y_select.value = self.column_names[1] if len(self.column_names) > 1 else self.column_names[0]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss(None)
            return

        if event.button.id == "confirm_btn":
            x_select = self.query_one("#x_select", Select)
            y_select = self.query_one("#y_select", Select)

            if isinstance(x_select.value, str) and isinstance(y_select.value, str):
                self.dismiss((x_select.value, y_select.value))

    def action_cancel(self) -> None:
        self.dismiss(None)


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
            yield Button("Set variables", id="set_variables")
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
        if not self.path:
            self.query_one("#status", Static).update("Load a CSV file first.")
            return

        try:
            column_names = read_csv_headers(self.path)
        except OSError as error:
            self.query_one("#status", Static).update(f"Could not read file: {error}")
            return

        if len(column_names) < 2:
            self.query_one("#status", Static).update("Need at least two columns to choose x and y.")
            return

        self.push_screen(VariableSelectionScreen(column_names), self._on_variables_picked)

    def _on_variables_picked(self, selection: tuple[str, str] | None) -> None:
        if selection is None:
            return

        if not self.path:
            self.query_one("#status", Static).update("Load a CSV file first.")
            return

        x_name, y_name = selection

        try:
            x_values, y_values = read_csv_columns(self.path, x_name, y_name)
        except OSError as error:
            self.query_one("#status", Static).update(f"Could not read file: {error}")
            return

        if not x_values or not y_values:
            self.query_one("#status", Static).update("No numeric rows found for the selected variables.")
            return

        self.x_name = x_name
        self.y_name = y_name
        self.x_variable = x_values
        self.y_variable = y_values
        self.query_one("#status", Static).update(f"X: {x_name} | Y: {y_name}")
    
    def plot(self):
        import numpy as np

        if not (self.path and self.x_name and self.y_name and self.x_variable and self.y_variable):
            self.query_one("#status", Static).update("Load a file and choose x and y variables first.")
            return

        x_values = np.asarray(self.x_variable, dtype=float)
        y_values = np.asarray(self.y_variable, dtype=float)

        m, b = np.polyfit(x_values, y_values, 1)
        y_fit = m * x_values + b

        plt.figure(figsize=(8, 5))
        plt.scatter(x_values, y_values, marker="o")
        plt.plot(x_values, y_fit, color="red", label=f"{self.y_name}={m:.2f}{self.x_name}+{b:.2f}")
        plt.xlabel(self.x_name)
        plt.ylabel(self.y_name)
        plt.title(f"{self.y_name} vs {self.x_name}")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    TUIApp().run()