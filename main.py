import argparse
import csv, statistics
import operator
from abc import ABC, abstractmethod
import logging

from tabulate import tabulate


class Report(ABC):
    _registry = dict()

    def __init__(self, *filenames):
        self.aggregated_data = dict()
        self.filenames = filenames

    def __init_subclass__(cls, **kwargs):  # Автоматическая регистрация подклассов для облегчения добавления новых отчетов
        super().__init_subclass__(**kwargs)
        key = getattr(cls, 'report_name', None)
        if key is not None:
            Report._registry[key] = cls

    @abstractmethod
    def create_report(self):
        pass

    @classmethod
    def prepare_report(cls, key: str, *args, **kwargs):
        try:
            report_object = cls._registry[key](*args, **kwargs)
        except KeyError:
            report_object = None
        return report_object


class MedianReport(Report):
    report_name = "median-coffee"

    def read_one_file(self, filename: str):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    student = row['student']
                    coffe_spent = int(row['coffee_spent'])
                    if student in self.aggregated_data.keys():
                        self.aggregated_data[student].append(coffe_spent)
                    else:
                        self.aggregated_data[student] = [coffe_spent]
        except FileNotFoundError:
            print("Такого файла не существует!")
            return

    def find_medians(self):
        return {student: statistics.median(data) for student, data in self.aggregated_data.items()}

    def create_report(self):
        for filename in self.filenames:
            self.read_one_file(filename)
        medians = sorted(self.find_medians().items(), key=operator.itemgetter(1), reverse=True)
        return medians


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data aggregation tool")
    parser.add_argument("--files", required=True, nargs="+")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    report = Report.prepare_report(args.report, *args.files)
    print(tabulate(report.create_report()))
