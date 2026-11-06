"""Export a Postman collection or verify it using real HTTP requests."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
from uuid import uuid4


ROOT = Path(__file__).resolve().parent.parent
COLLECTION = ROOT / "postman/LAB08.postman_collection.json"


def cases():
    items = []

    def add(name, method, path, status, body=None, capture=None, field=None):
        items.append(dict(name=name, method=method, path=path, status=status,
                          body=body, capture=capture, field=field))

    options = [
        {"text": "A language", "is_correct": True},
        {"text": "A database", "is_correct": False},
    ]
    question = {"exam": "{{exam_id}}", "text": "Python {{run_tag}}",
                "options": options}
    add("01 Create isolated exam", "POST", "/api/exams/", 201,
        {"title": "HTTP lab {{run_tag}}"}, {"exam_id": "id"})
    add("02 List exams", "GET", "/api/exams/", 200)
    add("03 Exam detail", "GET", "/api/exams/{{exam_id}}/", 200)
    add("04 Patch exam", "PATCH", "/api/exams/{{exam_id}}/", 200,
        {"title": "HTTP lab updated {{run_tag}}"})
    add("05 Create nested question", "POST", "/api/questions/", 201,
        question, {"question_id": "id", "correct_id": "options.0.id"})
    for index in range(2, 12):
        body = dict(question, text=f"Python {{{{run_tag}}}} item {index}")
        add(f"06.{index:02} Create pagination question", "POST",
            "/api/questions/", 201, body)
    add("07 List questions", "GET", "/api/questions/", 200)
    add("08 Question detail", "GET", "/api/questions/{{question_id}}/", 200)
    add("09 Patch question without options", "PATCH",
        "/api/questions/{{question_id}}/", 200,
        {"text": "Python {{run_tag}} edited"})
    add("10 Create incorrect option", "POST", "/api/options/", 201,
        {"question": "{{question_id}}", "text": "Extra", "is_correct": False},
        {"option_id": "id"})
    add("11 List options", "GET", "/api/options/", 200)
    add("12 Option detail", "GET", "/api/options/{{option_id}}/", 200)
    add("13 Patch option", "PATCH", "/api/options/{{option_id}}/", 200,
        {"text": "Extra edited"})
    add("14 Filter by exam", "GET", "/api/questions/?exam={{exam_id}}", 200)
    add("15 Search question text", "GET",
        "/api/questions/?search={{run_tag}}", 200)
    add("16 Pagination page two", "GET", "/api/questions/?page=2", 200)
    add("17 Combined filter search page two", "GET",
        "/api/questions/?exam={{exam_id}}&search={{run_tag}}&page=2", 200)
    add("18 Missing required title", "POST", "/api/exams/", 400, {},
        field="title")
    add("19 Incorrect exam type", "POST", "/api/questions/", 400,
        dict(question, exam="not-an-id"), field="exam")
    add("20 No correct option", "POST", "/api/questions/", 400,
        dict(question, options=[{"text": "No", "is_correct": False}]),
        field="options")
    add("21 Two correct options", "POST", "/api/questions/", 400,
        dict(question, options=[{"text": "A", "is_correct": True},
                                {"text": "B", "is_correct": True}]),
        field="options")
    add("22 Invalid exam filter", "GET", "/api/questions/?exam=invalid", 400,
        field="exam")
    add("23 Missing page", "GET",
        "/api/questions/?exam={{exam_id}}&page=999999", 404, field="detail")
    add("24 Reject second correct option", "POST", "/api/options/", 400,
        {"question": "{{question_id}}", "text": "Bad", "is_correct": True},
        field="options")
    add("25 Reject unmarking correct option", "PATCH",
        "/api/options/{{correct_id}}/", 400, {"is_correct": False},
        field="options")
    add("26 Reject deleting correct option", "DELETE",
        "/api/options/{{correct_id}}/", 400, field="options")
    add("27 Delete incorrect option", "DELETE",
        "/api/options/{{option_id}}/", 204)
    add("28 Deleted option is missing", "GET",
        "/api/options/{{option_id}}/", 404, field="detail")
    add("29 Delete question", "DELETE",
        "/api/questions/{{question_id}}/", 204)
    add("30 Deleted question is missing", "GET",
        "/api/questions/{{question_id}}/", 404, field="detail")
    add("31 Delete isolated exam and remaining questions", "DELETE",
        "/api/exams/{{exam_id}}/", 204)
    add("32 Deleted exam is missing", "GET",
        "/api/exams/{{exam_id}}/", 404, field="detail")
    return items


def export_collection(items):
    exported = []
    for case in items:
        tests = [
            f'pm.test("HTTP {case["status"]}", function () {{',
            f'    pm.response.to.have.status({case["status"]});',
            '});',
        ]
        if case["status"] != 204:
            tests.append('const data = pm.response.json();')
            tests.extend([
                'pm.test("JSON response", function () {',
                '    pm.expect(pm.response.headers.get("Content-Type"))',
                '        .to.include("application/json");',
                '});',
            ])
        if case["field"]:
            tests.append(
                'pm.test("Validation field", function () { '
                f'pm.expect(data).to.have.property("{case["field"]}"); }});'
            )
        if case["status"] in [200, 201]:
            tests.extend([
                'pm.test("Resource or paginated response", function () {',
                '    if (Array.isArray(data.results)) {',
                '        pm.expect(data.count).to.be.a("number");',
                '        pm.expect(data.results.length).to.be.at.most(10);',
                '        pm.expect(data).to.have.property("next");',
                '        pm.expect(data).to.have.property("previous");',
                '    } else { pm.expect(data.id).to.be.a("number"); }',
                '});',
                'pm.test("Nested question integrity", function () {',
                '    const rows = data.results || [data];',
                '    rows.forEach(function (row) {',
                '        if (Array.isArray(row.options)) {',
                '            pm.expect(row.exam).to.be.a("number");',
                '            pm.expect(row.options.filter(x => x.is_correct)',
                '                .length).to.equal(1);',
                '        }',
                '    });',
                '});',
            ])
        if case["name"].startswith(("14 ", "15 ", "17 ")):
            tests.append(
                'pm.test("Isolated result count", function () { '
                'pm.expect(data.count).to.equal(11); });'
            )
        if case["name"].startswith("17 "):
            tests.extend([
                'pm.test("Combined second page", function () {',
                '    pm.expect(data.results.length).to.equal(1);',
                '    pm.expect(data.next).to.equal(null);',
                '    pm.expect(data.previous).to.be.a("string");',
                '    data.results.forEach(function (row) {',
                '        pm.expect(String(row.exam)).to.equal(',
                '            pm.collectionVariables.get("exam_id"));',
                '    });',
                '});',
            ])
        for variable, expression in (case["capture"] or {}).items():
            expression = re.sub(r"\.(\d+)", r"[\1]", expression)
            tests.append(
                f'pm.collectionVariables.set("{variable}", '
                f'String(data.{expression}));'
            )
        request = {
            "method": case["method"],
            "header": [{"key": "Accept", "value": "application/json"}],
            "url": "{{base_url}}" + case["path"],
            "description": (
                "Ejecutar en orden; utiliza datos aislados de esta ejecución."
            ),
        }
        if case["body"] is not None:
            request["header"].append(
                {"key": "Content-Type", "value": "application/json"}
            )
            request["body"] = {
                "mode": "raw", "raw": json.dumps(case["body"], indent=2),
                "options": {"raw": {"language": "json"}},
            }
        entry = {"name": case["name"], "request": request,
                 "event": [{"listen": "test", "script": {
                     "type": "text/javascript", "exec": tests,
                 }}]}
        if not exported:
            entry["event"].insert(0, {"listen": "prerequest", "script": {
                "type": "text/javascript", "exec": [
                    'pm.collectionVariables.set("run_tag", '
                    '"lab08_" + pm.variables.replaceIn("{{$guid}}"));',
                    'for (const key of ["exam_id", "question_id",',
                    '    "option_id", "correct_id"]) {',
                    '    pm.collectionVariables.unset(key);',
                    '}',
                ],
            }})
        exported.append(entry)
    collection = {
        "info": {
            "name": "Laboratorio 08 - Django REST",
            "schema": (
                "https://schema.getpostman.com/json/collection/v2.1.0/"
                "collection.json"
            ),
            "description": (
                "Ejecutar toda la colección en orden. Crea datos propios, "
                "prueba CRUD y errores, y elimina solo esos datos. "
                "No ejecutar solicitudes destructivas aisladas "
                "con IDs manuales."
            ),
        },
        "variable": [{"key": "base_url", "value": "http://127.0.0.1:8000"}],
        "item": exported,
    }
    COLLECTION.parent.mkdir(exist_ok=True)
    COLLECTION.write_text(json.dumps(collection, ensure_ascii=False, indent=2)
                          + "\n", encoding="utf-8")
    print(f"Exported {len(items)} requests to {COLLECTION}")


def substitute(value, variables):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(variables[m[1]]), value)


def run(items, base_url):
    variables = {"run_tag": "lab08_" + uuid4().hex}
    results = []
    try:
        for case in items:
            path = substitute(case["path"], variables)
            body = case["body"]
            if body is not None:
                body = substitute(json.dumps(body), variables).encode()
            headers = {"Accept": "application/json"}
            if body is not None:
                headers["Content-Type"] = "application/json"
            request = urllib.request.Request(
                base_url + path, data=body, method=case["method"],
                headers=headers,
            )
            try:
                response = urllib.request.urlopen(request, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                raw = response.read()
                data = json.loads(raw) if raw else None
                result = {"name": case["name"], "method": case["method"],
                          "path": path, "expected": case["status"],
                          "status": response.status, "response": data}
                results.append(result)
                assert response.status == case["status"], result
                if case["field"]:
                    assert case["field"] in data, result
                if case["status"] in [200, 201]:
                    assert "application/json" in response.headers[
                        "Content-Type"
                    ]
                    if "results" in data:
                        assert isinstance(data["count"], int)
                        assert len(data["results"]) <= 10
                        assert "next" in data and "previous" in data
                    else:
                        assert isinstance(data["id"], int)
                    for row in data.get("results", [data]):
                        if "options" in row:
                            assert isinstance(row["exam"], int)
                            assert sum(
                                o["is_correct"] for o in row["options"]
                            ) == 1
                if case["name"].startswith(("14 ", "15 ", "17 ")):
                    assert data["count"] == 11, result
                if case["name"].startswith("17 "):
                    assert len(data["results"]) == 1
                    assert data["next"] is None
                    assert data["previous"] is not None
                    assert all(str(q["exam"]) == variables["exam_id"]
                               for q in data["results"])
                for variable, expression in (case["capture"] or {}).items():
                    value = data
                    for key in expression.split("."):
                        value = (
                            value[int(key)] if key.isdigit() else value[key]
                        )
                    variables[variable] = str(value)
                result["checks_passed"] = True
                print(f'{case["method"]} {path} -> {response.status}')
    finally:
        report = {
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "client": "Python urllib.request (real HTTP; not Postman)",
            "base_url": base_url, "variables": variables,
            "results": results,
            "completed": len(results) == len(items)
                         and all(r.get("checks_passed") for r in results),
        }
        output = ROOT / "docs/HTTP_RESULTS.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)
                          + "\n", encoding="utf-8")
        print(f"Recorded {len(results)} responses in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.export:
        export_collection(cases())
    else:
        run(cases(), args.base_url.rstrip("/"))
