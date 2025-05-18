# School Manager Project

## Description
This project is a school management system built with Django. It includes modules for managing students (alunos), teachers (professores), reports (relatorios), and user authentication. The system provides functionalities such as student registration, grade management, scheduling, and reporting.

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd school_manager_project
   ```
3. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Apply database migrations:
   ```
   python manage.py migrate
   ```
2. Run the development server:
   ```
   python manage.py runserver
   ```
3. Access the application in your browser at `http://127.0.0.1:8000/`.

## Contributing
Contributions are welcome. Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License.
