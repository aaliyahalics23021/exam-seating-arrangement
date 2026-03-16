from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

from fitness import Student, to_seat_cards
from genetic_algorithm import GAConfig, optimize_seating_ga


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_CSV = BASE_DIR / "sample_students.csv"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/input")
    def input_page():
        return render_template("input.html")

    @app.get("/download/sample")
    def download_sample():
        return send_file(SAMPLE_CSV, as_attachment=True, download_name="sample_students.csv")

    @app.get("/api/sample_students")
    def api_sample_students():
        df = pd.read_csv(SAMPLE_CSV)
        return jsonify({"students": df.to_dict(orient="records")})

    def _parse_students_from_csv_bytes(content: bytes) -> List[Student]:
        df = pd.read_csv(io.BytesIO(content))
        required = {"Student_ID", "Name", "Subject"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

        students: List[Student] = []
        for _, row in df.iterrows():
            sid = str(row["Student_ID"]).strip()
            name = str(row["Name"]).strip()
            subject = str(row["Subject"]).strip()
            if not sid or not name or not subject:
                continue
            students.append(Student(student_id=sid, name=name, subject=subject))
        if not students:
            raise ValueError("No valid students found in CSV.")
        return students

    def _get_students_from_request() -> Tuple[List[Student], str]:
        use_sample = request.form.get("use_sample") == "on"
        if use_sample:
            students = _parse_students_from_csv_bytes(SAMPLE_CSV.read_bytes())
            return students, "sample_students.csv"

        f = request.files.get("students_csv")
        if not f or f.filename == "":
            raise ValueError("Please upload a CSV file or use the sample students.")
        content = f.read()
        students = _parse_students_from_csv_bytes(content)
        return students, f.filename

    @app.post("/run")
    def run_ga():
        try:
            rows = int(request.form.get("rows", "6"))
            cols = int(request.form.get("cols", "6"))
            population_size = int(request.form.get("population_size", "80"))
            generations = int(request.form.get("generations", "100"))
            if rows <= 0 or cols <= 0:
                raise ValueError("Rows and Columns must be positive.")
            if population_size < 50 or population_size > 100:
                raise ValueError("Population size must be between 50 and 100.")
            if generations <= 0:
                raise ValueError("Generations must be positive.")

            students, source_name = _get_students_from_request()
            total_seats = rows * cols
            if total_seats < len(students):
                raise ValueError(
                    f"Not enough seats ({total_seats}) for students ({len(students)}). Increase rows/columns."
                )

            # Random baseline (initial random seating before GA optimization)
            import random

            baseline = list(range(len(students)))
            random.shuffle(baseline)

            config = GAConfig(population_size=population_size, generations=generations, mutation_rate=0.05)
            ga = optimize_seating_ga(students, rows, cols, config)
            best = ga["best_chromosome"]

            baseline_cards = to_seat_cards(baseline, students, rows, cols)
            optimized_cards = to_seat_cards(best, students, rows, cols)

            initial_clashes = int(baseline_cards["clash_count"])
            final_clashes = int(optimized_cards["clash_count"])
            clash_reduction = 0.0
            if initial_clashes > 0:
                clash_reduction = max(0.0, (initial_clashes - final_clashes) / initial_clashes * 100.0)

            return render_template(
                "simulation.html",
                rows=rows,
                cols=cols,
                source_name=source_name,
                total_students=len(students),
                total_seats=total_seats,
                population_size=ga["population_size"],
                generations_executed=ga["generations"],
                best_fitness=float(ga["best_fitness"]),
                history_best=ga["history_best"],
                history_avg=ga["history_avg"],
                baseline=baseline_cards,
                optimized=optimized_cards,
                initial_clashes=initial_clashes,
                final_clashes=final_clashes,
                clash_reduction=clash_reduction,
            )
        except Exception as e:
            return render_template("input.html", error=str(e)), 400

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)

