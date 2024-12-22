CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE DocumentType (
    Id uuid primary key, 
    Name text
);

CREATE TABLE Employee (
    Id uuid primary key,
    Surname text,
    Name text,
    Fathername text,
    Birthdate date,
    BirthPlace text,
    CitizenshipName text,
    Comment text
);

CREATE TABLE Document (
    Id uuid primary key,
    Number text,
    DocumentTypeId uuid,
    EmployeeId uuid,

    constraint FkDocumentType 
        foreign key(DocumentTypeId) 
            references DocumentType(Id),

    constraint FkEmployee
        foreign key(EmployeeId) 
            references Employee(Id)
);