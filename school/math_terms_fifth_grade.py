import random
import re
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================
# Einstellungen
# ============================================================

ANZAHL_AUFGABEN = 10
TERM_LENGTH = 2
MIN_SOLUTION = 0
MAX_SOLUTION = 11111
SPACE_FOR_TASK = "\\vspace{50pt}"

# ============================================================
# Hilfsfunktionen
# ============================================================

def choice(seq):
    return random.choice(seq)


# ============================================================
# Gute Zahlenkombinationen
# ============================================================

POWER_BASES = [2, 3, 4, 5, 6]

POWER_EXPONENTS = {
    2: [0, 1, 2, 3, 4, 5, 6],
    3: [1, 2, 3],
    4: [1, 2, 3],
    5: [0, 1, 2, 3],
    6: [0, 1, 2]
}

DIVISION_PAIRS = [
    (4, 2), (6, 2), (6, 3), (8, 2), (8, 4),
    (9, 3), (10, 2), (10, 5),
    (12, 2), (12, 3), (12, 4), (12, 6),
    (14, 2), (14, 7),
    (15, 3), (15, 5),
    (16, 2), (16, 4), (16, 8),
    (18, 2), (18, 3), (18, 6), (18, 9),
    (20, 2), (20, 4), (20, 5), (20, 10),
    (21, 3), (21, 7),
    (24, 2), (24, 3), (24, 4), (24, 6), (24, 8),
    (27, 3), (27, 9),
    (28, 2), (28, 4), (28, 7),
    (30, 2), (30, 3), (30, 5), (30, 6), (30, 10),
    (32, 2), (32, 4), (32, 8),
    (36, 2), (36, 3), (36, 4), (36, 6), (36, 9),
    (40, 2), (40, 4), (40, 5), (40, 8), (40, 10),
    (42, 2), (42, 3), (42, 6), (42, 7),
    (48, 2), (48, 3), (48, 4), (48, 6), (48, 8), (48, 12),
    (54, 2), (54, 3), (54, 6), (54, 9),
    (56, 2), (56, 4), (56, 7), (56, 8),
    (63, 3), (63, 7), (63, 9),
    (64, 2), (64, 4), (64, 8),
    (72, 2), (72, 3), (72, 4), (72, 6), (72, 8), (72, 9),
    (81, 3), (81, 9),
]
DIVISION_PAIRS += [
    (60, 2), (60, 3), (60, 4), (60, 5), (60, 6), (60, 10),
    (80, 2), (80, 4), (80, 5), (80, 8),
    (90, 2), (90, 3), (90, 5), (90, 6), (90, 9),
    (100, 2), (100, 4), (100, 5), (100, 10),
]


MULTIPLICATION_PAIRS = [
    (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10),
    (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10),
    (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10),
    (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10),
    (6, 6), (6, 7), (6, 8), (6, 9), (6, 10),
    (7, 7), (7, 8), (7, 9), (7, 10),
    (8, 8), (8, 9), (8, 10),
    (9, 9), (9, 10),
    (10, 10),
]
MULTIPLICATION_PAIRS += [
    (11, 2), (11, 3), (11, 4),
    (12, 2), (12, 3), (12, 4),
    (15, 2), (15, 3),
    (20, 2),
    (25, 2)
]

# ============================================================
# Termgenerator
# ============================================================

def generate_power():
    base = choice(POWER_BASES)
    exponent = choice(POWER_EXPONENTS[base])

    return f"{base}^{exponent}"


def generate_division():
    a, b = choice(DIVISION_PAIRS)

    # Sicherheit: nur echte ganzzahlige Divisionen zulassen
    if a % b != 0:
        a = b * random.randint(2, 12)

    return f"{a} \\div {b}"


def generate_multiplication():
    a, b = choice(MULTIPLICATION_PAIRS)

    if random.random() < 0.3:
        return f"({a} \\cdot {b})"

    return f"{a} \\cdot {b}"


def generate_add_sub_term():

    parts = []

    parts.append(str(random.randint(10, 120)))

    for _ in range(TERM_LENGTH):

        op = choice(["+", "-"])

        structure = choice([
            "power_mult",
            "division",
            "multiplication",
            "number"
        ])

        if structure == "power_mult":

            part = (
                f"{generate_power()} "
                f"\\cdot "
                f"{random.randint(2, 8)}"
            )

        elif structure == "division":

            if random.random() < 0.4:

                a, b = choice(DIVISION_PAIRS)
                c, d = choice(MULTIPLICATION_PAIRS)

                part = (
                    f"{a} "
                    f"\\div "
                    f"({c} \\cdot {d})"
                )

            else:
                part = generate_division()

        elif structure == "multiplication":
            part = generate_multiplication()

        else:
            part = str(random.randint(5, 60))

        parts.append(f"{op} {part}")

    return " ".join(parts)


def generate_inner_parentheses():

    variant = choice([
        "simple",
        "mixed",
        "powers"
    ])

    if variant == "simple":

        a = random.randint(2, 12)
        b = random.randint(2, 12)
        c = random.randint(2, 8)

        return f"{a} + {b} \\cdot {c}"

    elif variant == "mixed":

        return generate_add_sub_term()

    else:

        return (
            f"{generate_power()} + "
            f"{generate_power()} - "
            f"{generate_division()}"
        )


def generate_expression():

    start = str(random.randint(5, 25))

    middle = generate_add_sub_term()

    expr = f"{start} + ({middle})"

    if random.random() < 0.9:

        structure = choice([
            "division_block",
            "multiplication_block",
            "nested"
        ])

        if structure == "division_block":

            left = generate_inner_parentheses()
            right = generate_inner_parentheses()

            expr += (
                f" + "
                f"({left}) "
                f"\\div "
                f"({right})"
            )

        elif structure == "multiplication_block":

            left = generate_inner_parentheses()
            right = generate_inner_parentheses()

            expr += (
                f" \\cdot "
                f"({left} + {right})"
            )

        else:

            left = generate_inner_parentheses()
            right = generate_inner_parentheses()

            expr += (
                f" + "
                f"(({left}) - ({right}))"
            )

    return expr


# ============================================================
# Berechnung
# ============================================================

def latex_to_python(expr):

    expr = expr.replace("\\cdot", "*")
    expr = expr.replace("\\div", "/")
    expr = expr.replace("^", "**")

    return expr

def safe_eval(expr):
    expr = latex_to_python(expr)

    # nur erlaubte Zeichen
    if not re.match(r'^[0-9+\-*/(). **]+$', expr.replace(" ", "")):
        raise ValueError("Ungültiger Ausdruck")

    result = eval(expr)

    if not isinstance(result, (int, float)):
        raise ValueError("Kein Zahlenergebnis")

    # harte Ganzzahlregel
    if result != int(result):
        raise ValueError("Nicht ganzzahlig")

    return int(result)

def calculate_expression(expr):
    return safe_eval(expr)


def is_valid_expression(expr):

    # Klammern prüfen
    counter = 0

    for char in expr:

        if char == "(":
            counter += 1

        elif char == ")":
            counter -= 1

        if counter < 0:
            return False

    if counter != 0:
        return False

    # Testweise berechnen
    try:
        calculate_expression(expr)
    except Exception:
        return False

    return True

# ============================================================
# Markdown erzeugen
# ============================================================

def create_markdown(tasks, solutions, timestamp):

    md = []

    md.append(f"# Übungsblatt Mathematik 5. Klasse: Terme")
    md.append("")
    md.append(f"Erstellt am: {timestamp}")
    md.append("")
    md.append("")
    md.append("## Aufgaben")
    md.append("")

    for i, task in enumerate(tasks, start=1):

        md.append(f"### Blatt {timestamp} Aufgabe {i}")
        md.append("")
        md.append(f"${task} =$  \n  \n  \n  ")
        md.append(SPACE_FOR_TASK)

    md.append("\\newpage")
    md.append("")
    md.append(f"# Lösungen")
    md.append("")

    for i, (task, solution) in enumerate(
        zip(tasks, solutions),
        start=1
    ):

        md.append(f"### Blatt {timestamp} Aufgabe {i}")
        md.append("")
        md.append(f"${task} = {solution}$")
        md.append("")
        md.append("")

    return "\n".join(md)


# ============================================================
# PDF erzeugen
# ============================================================

def create_pdf(md_filename):

    pdf_filename = md_filename.replace(".md", ".pdf")

    command = [
        "pandoc",
        md_filename,
        "-o",
        pdf_filename
    ]

    subprocess.run(command, check=True)

    return pdf_filename


# ============================================================
# Hauptprogramm
# ============================================================

def main():

    random.seed()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    tasks = []
    solutions = []

    while len(tasks) < ANZAHL_AUFGABEN:

        expr = generate_expression()

        try:
            solution = calculate_expression(expr)

            if isinstance(solution, int) and solution >= MIN_SOLUTION and solution < MAX_SOLUTION:

                tasks.append(expr)
                solutions.append(solution)

        except Exception:
            continue

    markdown = create_markdown(
        tasks,
        solutions,
        timestamp
    )

    md_filename = f"Termaufgaben_{timestamp}.md"

    Path(md_filename).write_text(
        markdown,
        encoding="utf-8"
    )

    print(f"Markdown-Datei erstellt: {md_filename}")

    try:

        pdf_filename = create_pdf(md_filename)

        print(f"PDF erstellt: {pdf_filename}")

    except FileNotFoundError:

        print("")
        print("Pandoc wurde nicht gefunden.")
        print("Installiere Pandoc:")
        print("https://pandoc.org/installing.html")

    except subprocess.CalledProcessError:

        print("")
        print("Fehler bei der PDF-Erstellung.")
        print("Wahrscheinlich fehlt eine LaTeX-Installation.")
        print("Empfehlung:")
        print("- MiKTeX (Windows)")
        print("- TeX Live (Linux/macOS)")


if __name__ == "__main__":
    main()