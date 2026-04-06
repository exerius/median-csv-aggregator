import pytest
import csv
import statistics
import tempfile
import os
from main import Report, MedianReport  # замените на реальное имя модуля


@pytest.fixture
def csv_file():
    """Создаёт временный CSV-файл и возвращает его имя. Удаляет после теста."""

    def _create_file(rows, fieldnames=['student', 'coffee_spent']):
        fd, filename = tempfile.mkstemp(suffix='.csv', text=True)
        os.close(fd)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return filename

    yield _create_file
    # После теста удаляем все созданные файлы (это можно улучшить, но для простоты так)
    # В реальном коде лучше хранить список файлов, но здесь каждый вызов создаёт новый.


@pytest.fixture
def multi_csv(csv_file):
    """Создаёт несколько CSV-файлов и возвращает их список."""

    def _make_files(data_list):
        files = []
        for i, rows in enumerate(data_list):
            fname = csv_file(rows)
            files.append(fname)
        return files

    return _make_files


def test_subclass_registration():
    assert "median-coffee" in Report._registry
    assert Report._registry["median-coffee"] is MedianReport


def test_prepare_report():
    report = Report.prepare_report("median-coffee", "dummy.csv")
    assert isinstance(report, MedianReport)
    assert report.filenames == ("dummy.csv",)

    report_none = Report.prepare_report("non-existent")
    assert report_none is None


def test_read_one_file(csv_file):
    rows = [
        {"student": "Alice", "coffee_spent": "3"},
        {"student": "Bob", "coffee_spent": "5"},
        {"student": "Alice", "coffee_spent": "7"}
    ]
    filename = csv_file(rows)
    report = MedianReport(filename)
    report.read_one_file(filename)
    assert report.aggregated_data == {"Alice": [3, 7], "Bob": [5]}
    os.unlink(filename)


def test_find_medians():
    report = MedianReport()
    report.aggregated_data = {
        "Alice": [3, 7, 8],
        "Bob": [5, 10],
        "Charlie": [1, 2, 3, 4, 100]
    }
    medians = report.find_medians()
    expected = {
        "Alice": statistics.median([3, 7, 8]),
        "Bob": statistics.median([5, 10]),
        "Charlie": statistics.median([1, 2, 3, 4, 100])
    }
    assert medians == expected


def test_create_report(multi_csv):
    data_files = [
        [{"student": "Alice", "coffee_spent": "3"}, {"student": "Bob", "coffee_spent": "5"}],
        [{"student": "Alice", "coffee_spent": "7"}, {"student": "Bob", "coffee_spent": "1"},
         {"student": "Charlie", "coffee_spent": "10"}]
    ]
    files = multi_csv(data_files)
    report = MedianReport(*files)
    result = report.create_report()
    # Ожидаемые медианы: Charlie=10, Alice=5, Bob=3
    assert result == [("Charlie", 10), ("Alice", 5), ("Bob", 3)]
    for f in files:
        os.unlink(f)


def test_file_not_found(capsys):
    report = MedianReport("non_existent_file.csv")
    report.read_one_file("non_existent_file.csv")
    captured = capsys.readouterr()
    assert "Такого файла не существует!" in captured.out
    assert report.aggregated_data == {}


def test_missing_column(csv_file):
    """Проверяем, что при отсутствии колонки 'coffee_spent' возникает KeyError."""
    # Создаём файл с другими заголовками
    rows = [{"student": "Alice", "cups": "3"}]
    filename = csv_file(rows, fieldnames=['student', 'cups'])
    report = MedianReport(filename)
    with pytest.raises(KeyError):
        report.read_one_file(filename)
    os.unlink(filename)


def test_invalid_value(csv_file):
    """Проверяем, что при нечисловом coffee_spent возникает ValueError."""
    rows = [{"student": "Alice", "coffee_spent": "not_a_number"}]
    filename = csv_file(rows)
    report = MedianReport(filename)
    with pytest.raises(ValueError):
        report.read_one_file(filename)
    os.unlink(filename)


def test_empty_files(csv_file):
    rows = []
    filename = csv_file(rows)
    report = MedianReport(filename)
    result = report.create_report()
    assert result == []
    os.unlink(filename)


def test_single_file_repeated(csv_file):
    rows = [
        {"student": "Alice", "coffee_spent": "10"},
        {"student": "Alice", "coffee_spent": "20"},
        {"student": "Alice", "coffee_spent": "30"}
    ]
    filename = csv_file(rows)
    report = MedianReport(filename)
    result = report.create_report()
    assert result == [("Alice", 20)]
    os.unlink(filename)


def test_sorting_descending(csv_file):
    rows = [
        {"student": "A", "coffee_spent": "1"},
        {"student": "B", "coffee_spent": "100"},
        {"student": "C", "coffee_spent": "50"}
    ]
    filename = csv_file(rows)
    report = MedianReport(filename)
    result = report.create_report()
    assert result == [("B", 100), ("C", 50), ("A", 1)]
    os.unlink(filename)