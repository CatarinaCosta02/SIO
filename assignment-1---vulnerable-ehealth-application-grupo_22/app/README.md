# eHealth Corp - Insecure App

## Description

This is a simple web application for a health clinic, written in **Flask** using 
**Python3.8** and **MySQL** for data persistence. The goal of this application 
is to show a set of vulnerabilities often found in software projects, that may 
be used to compromise the application or the system.

Developed within the scope of the first group project of Security of Information
and Organizations (2022/2023).

## Authors
This project was done by:

| Name           |  NMEC  |         Email         |
| :-------------:|:------:|:---------------------:|
| Catarina Costa | 103696 | catarinateves02@ua.pt |
| Diogo Paiva    | 103183 |  diogopaiva21@ua.pt   |
| João Fonseca   | 103154 |  joao.fonseca@ua.pt   |
| Jorge SIlva    | 103865 |   jorgetsilva@ua.pt   |

The front-end was based on [this](https://themewagon.com/themes/free-bootstrap-4-html-5-healthcare-website-template-novena/) template by Themefisher.

## Dependencies

This application was devoleped using **Python3.8** and requires the following
dependencies (automatically installed inside docker):

- flask (2.2.2)
- flask-mysqldb (1.0.1)
- flask-login (0.6.2)

## Running the Application and Database (with docker)

- Run `docker compose up` in root. 
- The application should be running on [localhost:5000](http://localhost:5000/).
- Access [localhost:5000/reset-db](http://localhost:5000/reset-db) to create the database (first time only).
- Stop the application and database using `CTRL+C` in terminal.

## Troubleshooting
- In case of errors, access [localhost:5000/reset-db](http://localhost:5000/reset-db) to reset the database.
