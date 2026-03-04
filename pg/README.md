# README for libs/pg

## Overview
The `libs/pg` package provides utilities and abstractions for interacting with PostgreSQL databases. It includes modules for database models, schemas, and controllers, making it easier to manage and query data.

## Features
- **Database Models**: Define and manage PostgreSQL tables using SQLAlchemy.
- **Controllers**: Handle CRUD operations and business logic.
- **Schemas**: Validate and serialize data using Pydantic.
- **Utilities**: Helper functions for common database operations.

## Installation
To use the `libs/pg` package, ensure you have the following dependencies installed:

- Python 3.8 or higher
- SQLAlchemy
- Pydantic

## Usage

### Setting Up the Database
1. Configure the database settings in `settings.py`.
2. Run migrations using Alembic to set up the database schema:

```bash
uv run alembic upgrade head
```

### Example: Using a Controller
Here is an example of how to use a controller to fetch data:


## Development

### Code Style
Ensure your code adheres to PEP 8 standards. Use tools like `black` and `flake8` for formatting and linting:

```bash
black .
flake8 .
```

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
