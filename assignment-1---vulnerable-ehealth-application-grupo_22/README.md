# eHealth Corp

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

## Implemented Vulnerabilities

- [CWE-22] Improper Limitation of a Pathname to a Restricted Directory ("Path Traversal")
- [CWE-79] Improper Neutralization of Input During Web Page Generation ("Cross-site Scripting")
- [CWE-89] Improper Neutralization of Special Elements used in an SQL Command ("SQL Injection")
- [CWE-211] Externally-Generated Error Message Containing Sensitive Information
- [CWE-352] Cross-site Request Forgery (CSRF)
- [CWE-552] Files or Directories Accessible to External Parties