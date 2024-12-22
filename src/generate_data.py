from faker import Faker
import uuid
import random
import psycopg
from typing import Optional


fake = Faker("ru_RU")

POSTGRESQL_CONFIG = {
    "dbname": "employees",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

N_EMPLOYEES = 10_000_000
COMMIT_STEP = 10_000
NULL_PROBABILITY = 0.2
MAX_DOCUMENTS = 3

INSERT_EMPLOYEE_SQL = """
INSERT INTO Employee (
    Id, Surname, Name, Fathername, Birthdate, BirthPlace, CitizenshipName, Comment
) VALUES (%s, %s, %s, %s, TO_DATE(%s, 'DD.MM.YYYY'), %s, %s, %s);
"""

INSERT_DOCUMENT_SQL = """
INSERT INTO Document (
    Id, DocumentTypeId, EmployeeId, Number
) VALUES (%s, %s, %s, %s);
"""


def is_null() -> bool:
    """
    Returns True with a probability defined by NULL_PROBABILITY, indicating
    whether a field should be NULL.
    """
    return random.random() < NULL_PROBABILITY


def safe_str(value: Optional[str], can_be_null: bool = True) -> str:
    """
    Formats a string for PostgreSQL queries. Converts the value to a string
    enclosed in single quotes unless it should be NULL.

    Args:
        value: The string value to format.
        can_be_null: If True, the value can be set to NULL with some probability.

    Returns:
        A formatted string ready for SQL insertion.
    """
    if can_be_null and is_null():
        return None
    return value


def create_random_date() -> str:
    """
    Generates a random date string in the format DD.MM.YYYY.

    Returns:
        A randomly generated date as a string.
    """
    day = random.randint(1, 28)
    month = random.randint(1, 12)
    year = random.randint(1950, 2023)
    return f"{day:02d}.{month:02d}.{year}"


DOCUMENT_TYPES = {
    str(uuid.uuid4()): name
    for name in [
        "Паспорт",
        "Военный билет",
        "Справка",
        "ВНЖ",
        "Загранпаспорт",
        "Паспорт моряка",
        "Дипломатический паспорт",
        "Студенческий билет",
        "Свидетельство о рождении",
        "Удостоверение",
    ]
}

CITIZENSHIPS = [
    "Российская Федерация",
    "Республика Беларусь",
    "Республика Казахстан",
    "Республика Армения",
    "Бразилия",
]


class Employee:
    """
    Represents an Employee record with fields populated by the Faker library
    and other random data generators.
    """

    def __init__(self):
        self.id = safe_str(str(uuid.uuid4()), can_be_null=False)
        self.name = safe_str(fake.first_name())
        self.surname = safe_str(fake.last_name())
        self.fathername = safe_str(fake.middle_name())
        self.birth_place = safe_str(fake.address())
        self.birthdate = safe_str(create_random_date())
        self.citizenship_name = safe_str(random.choice(CITIZENSHIPS))
        self.comment = safe_str(fake.color_name())


class Document:
    """
    Represents a Document record associated with an Employee, with fields
    populated by random data.
    """

    def __init__(self, employee_id: str):
        self.id = safe_str(str(uuid.uuid4()), can_be_null=False)
        self.number = safe_str(fake.passport_number())
        self.type_id = safe_str(random.choice(list(DOCUMENT_TYPES.keys())))
        self.employee_id = employee_id


def insert_document_types(cursor):
    """
    Inserts predefined document types into the database.

    Args:
        cursor: A database cursor for executing the SQL queries.
    """
    values = ",\n".join(f"('{key}', '{value}')" for key, value in DOCUMENT_TYPES.items())
    cursor.execute(f"INSERT INTO DocumentType (Id, Name) VALUES\n{values};")


def generate_employees(cursor, connection):
    """
    Generates and inserts employee records in batches.

    Args:
        cursor: A database cursor for executing the SQL queries.
        connection: The database connection for committing transactions.

    Returns:
        A list of Employee objects representing all generated employees.
    """
    employees = []
    for i in range(N_EMPLOYEES):
        if i % COMMIT_STEP == 0:
            cursor.execute("BEGIN;")

        employee = Employee()
        employees.append(employee)
        cursor.execute(
            INSERT_EMPLOYEE_SQL,
            (
                employee.id,
                employee.surname,
                employee.name,
                employee.fathername,
                employee.birthdate,
                employee.birth_place,
                employee.citizenship_name,
                employee.comment,
            ),
        )

        if i % COMMIT_STEP == COMMIT_STEP - 1:
            connection.commit()
            print(f"Inserted {i + 1} employees.")
    return employees


def generate_documents(cursor, connection, employees):
    """
    Generates and inserts document records for employees in batches.

    Args:
        cursor: A database cursor for executing the SQL queries.
        connection: The database connection for committing transactions.
        employees: A list of Employee objects for which documents are generated.
    """
    for i, employee in enumerate(employees):
        if i % COMMIT_STEP == 0:
            cursor.execute("BEGIN;")

        if not is_null():
            num_docs = random.randint(1, MAX_DOCUMENTS)
            for _ in range(num_docs):
                document = Document(employee.id)
                cursor.execute(
                    INSERT_DOCUMENT_SQL,
                    (
                        document.id,
                        document.type_id,
                        document.employee_id,
                        document.number,
                    ),
                )

        if i % COMMIT_STEP == COMMIT_STEP - 1:
            connection.commit()
            print(f"Inserted documents for {i + 1} employees.")


def main():
    with psycopg.connect(**POSTGRESQL_CONFIG) as connection:
        with connection.cursor() as cursor:
            insert_document_types(cursor)
            connection.commit()

            employees = generate_employees(cursor, connection)
            generate_documents(cursor, connection, employees)


if __name__ == "__main__":
    main()