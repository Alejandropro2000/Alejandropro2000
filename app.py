from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

APP_TITLE = "InfoConfidencial PY"
DATA_PATH = Path(__file__).parent / "data" / "sample_records.json"


def load_records() -> dict[str, dict]:
    if not DATA_PATH.exists():
        return {}
    with DATA_PATH.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return {item["cedula"]: item for item in payload.get("records", [])}


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x700")
        self.minsize(900, 620)
        self.configure(bg="#f3f6fb")

        self.records = load_records()

        self._build_header()
        self._build_tabs()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#0b3c6f", padx=22, pady=16)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Servicio de Información Confidencial",
            bg="#0b3c6f",
            fg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Validación de Identidad por Cédula Paraguaya",
            bg="#0b3c6f",
            fg="#d6e8ff",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            header,
            text=(
                "Ubicabilidad para cobranzas • Disminución de riesgos en crédito • "
                "Historial de antecedentes para RRHH"
            ),
            bg="#0b3c6f",
            fg="#c3d8f6",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

    def _build_tabs(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=16)

        consulta_tab = tk.Frame(notebook, bg="#ffffff")
        datos_tab = tk.Frame(notebook, bg="#ffffff")
        beneficios_tab = tk.Frame(notebook, bg="#ffffff")

        notebook.add(consulta_tab, text="Consulta por Cédula")
        notebook.add(datos_tab, text="Datos Referenciales")
        notebook.add(beneficios_tab, text="Beneficios")

        self._build_consulta_tab(consulta_tab)
        self._build_datos_tab(datos_tab)
        self._build_beneficios_tab(beneficios_tab)

    def _build_consulta_tab(self, parent: tk.Frame) -> None:
        container = tk.Frame(parent, bg="#ffffff", padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Buscar persona por número de cédula",
            bg="#ffffff",
            fg="#0b3c6f",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")

        search_row = tk.Frame(container, bg="#ffffff")
        search_row.pack(fill="x", pady=(12, 16))

        self.cedula_var = tk.StringVar()
        entry = ttk.Entry(search_row, textvariable=self.cedula_var, width=35)
        entry.pack(side="left")

        ttk.Button(search_row, text="Consultar", command=self._on_search).pack(side="left", padx=(8, 0))
        ttk.Button(search_row, text="Limpiar", command=self._clear_result).pack(side="left", padx=(8, 0))

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=(0, 14))

        self.result_box = tk.Text(container, height=21, wrap="word", font=("Consolas", 10))
        self.result_box.pack(fill="both", expand=True)
        self.result_box.insert("1.0", "Ingresá una cédula y hacé clic en Consultar.\n")
        self.result_box.configure(state="disabled")

    def _build_datos_tab(self, parent: tk.Frame) -> None:
        container = tk.Frame(parent, bg="#ffffff", padx=22, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Datos referenciales que puede encontrar en la plataforma",
            bg="#ffffff",
            fg="#0b3c6f",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        items = [
            "Datos personales registrados en Identificaciones.",
            "Registro de personas fallecidas (actualización diaria en un % de los casos).",
            "Datos de hermanos (95% de cobertura en los casos disponibles).",
            "Datos de Cónyuges / Hijos (actualización diaria).",
            "Teléfonos de contacto (operadoras y/o referencias anteriores).",
            "Registro en IPS con beneficiarios, empleador y meses de aporte.",
            "Registro de cédulas duplicadas (33.600 cédulas expedidas por Identificaciones).",
            "Denuncias policiales.",
            "Funcionarios públicos: asignación, saldo disponible en BNF y otros.",
        ]

        for item in items:
            tk.Label(
                container,
                text=f"• {item}",
                anchor="w",
                justify="left",
                bg="#ffffff",
                fg="#233245",
                font=("Segoe UI", 10),
            ).pack(fill="x", pady=2)

    def _build_beneficios_tab(self, parent: tk.Frame) -> None:
        container = tk.Frame(parent, bg="#ffffff", padx=22, pady=20)
        container.pack(fill="both", expand=True)

        blocks = [
            (
                "UBICABILIDAD en cobranzas",
                "Permite localizar personas con alto porcentaje de efectividad usando datos de contacto y referencias.",
            ),
            (
                "DISMINUCIÓN DE RIESGOS",
                "Validación de datos al momento de otorgar crédito para decisiones más seguras.",
            ),
            (
                "Antecedentes para RRHH",
                "Apoya evaluaciones de personal con información histórica y señales de alerta.",
            ),
        ]

        for title, description in blocks:
            card = tk.Frame(container, bg="#f8fbff", bd=1, relief="solid", padx=14, pady=12)
            card.pack(fill="x", pady=8)

            tk.Label(card, text=title, bg="#f8fbff", fg="#0b3c6f", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(
                card,
                text=description,
                bg="#f8fbff",
                fg="#2f4155",
                font=("Segoe UI", 10),
                wraplength=760,
                justify="left",
            ).pack(anchor="w", pady=(4, 0))

    def _on_search(self) -> None:
        cedula = self.cedula_var.get().strip()
        if not cedula:
            messagebox.showwarning("Campo requerido", "Ingresá un número de cédula para consultar.")
            return

        record = self.records.get(cedula)
        if not record:
            self._write_result(
                f"No se encontraron registros para la cédula {cedula}.\n"
                "Tip: podés probar con cédulas demo: 4567890, 5234561 o 3322110."
            )
            return

        lines = [
            f"Cédula: {record['cedula']}",
            f"Nombre: {record['nombre']}",
            f"Estado civil: {record['estado_civil']}",
            f"Domicilio: {record['domicilio']}",
            f"Teléfonos: {', '.join(record.get('telefonos', [])) or 'Sin datos'}",
            f"IPS: empleador {record['ips']['empleador']} / meses aporte {record['ips']['meses_aporte']}",
            f"Beneficiarios IPS: {', '.join(record['ips'].get('beneficiarios', [])) or 'Sin datos'}",
            f"Denuncias policiales: {record.get('denuncias_policiales', 'Sin datos')}",
            f"Cédula duplicada: {'Sí' if record.get('cedula_duplicada') else 'No'}",
            f"Funcionariado público: {record.get('funcionario_publico', 'No')}",
            f"Observación RRHH: {record.get('observacion_rrhh', 'Sin observaciones')}",
        ]

        self._write_result("\n".join(lines))

    def _write_result(self, text: str) -> None:
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", tk.END)
        self.result_box.insert("1.0", text)
        self.result_box.configure(state="disabled")

    def _clear_result(self) -> None:
        self.cedula_var.set("")
        self._write_result("Ingresá una cédula y hacé clic en Consultar.\n")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
