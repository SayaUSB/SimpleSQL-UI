import sys
import mysql.connector
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QDialog,
                             QTableWidget, QTableWidgetItem, QMessageBox, 
                             QComboBox, QHBoxLayout, QFormLayout, QFileDialog)
from PyQt6.QtCore import Qt
import csv

def connect_database():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="rka_enterprise"
        )
        return db
    except mysql.connector.Error as err:
        QMessageBox.critical(None, "Database Connection Error", f"Error: {err}")
        return None

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 150)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.nrp_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Login")

        layout.addWidget(QLabel("ID:"))
        layout.addWidget(self.nrp_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.login_button.clicked.connect(self.login)

    def login(self):
        nrp = self.nrp_input.text()
        password = self.password_input.text()

        db = connect_database()
        if db:
            cursor = db.cursor()
            query = "SELECT * FROM staff WHERE id_staff = %s AND sandi = %s"
            cursor.execute(query, (nrp, password))
            result = cursor.fetchone()

            if result:
                self.close()
                self.db_window = DatabaseWindow(db)
                self.db_window.show()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid NRP or password")
            
            cursor.close()

class InsertDialog(QDialog):
    def __init__(self, parent=None, table_name=None, columns=None):
        super().__init__(parent)
        self.setWindowTitle(f"Insert into {table_name}")
        self.setGeometry(200, 200, 300, 200)
        
        layout = QFormLayout(self)
        self.inputs = {}
        
        for column in columns:
            if column[0] != 'id':  # Assuming 'id' is auto-increment
                self.inputs[column[0]] = QLineEdit(self)
                layout.addRow(QLabel(column[0]), self.inputs[column[0]])
        
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.accept)
        layout.addRow(self.submit_button)

class UpdateDialog(QDialog):
    def __init__(self, parent=None, table_name=None, columns=None, current_values=None):
        super().__init__(parent)
        self.setWindowTitle(f"Update {table_name}")
        self.setGeometry(200, 200, 300, 200)
        
        layout = QFormLayout(self)
        self.inputs = {}
        
        for column in columns:
            self.inputs[column[0]] = QLineEdit(self)
            if current_values and column[0] in current_values:
                self.inputs[column[0]].setText(str(current_values[column[0]]))
            layout.addRow(QLabel(column[0]), self.inputs[column[0]])
        
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.accept)
        layout.addRow(self.submit_button)

class DatabaseWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Database Operations")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # DDL Operations
        ddl_layout = QHBoxLayout()
        self.table_name_input = QLineEdit()
        self.create_table_button = QPushButton("Create Table")
        self.drop_table_button = QPushButton("Drop Table")
        ddl_layout.addWidget(QLabel("Table Name:"))
        ddl_layout.addWidget(self.table_name_input)
        ddl_layout.addWidget(self.create_table_button)
        ddl_layout.addWidget(self.drop_table_button)
        layout.addLayout(ddl_layout)

        # DML Operations
        dml_layout = QFormLayout()
        self.table_select = QComboBox()
        self.refresh_tables()
        self.column_select = QComboBox()
        self.value_input = QLineEdit()
        self.insert_button = QPushButton("Insert")
        self.delete_button = QPushButton("Delete")
        dml_layout.addRow("Select Table:", self.table_select)
        dml_layout.addRow("Select Column:", self.column_select)
        dml_layout.addRow("Value:", self.value_input)
        dml_layout.addRow(self.insert_button)
        dml_layout.addRow(self.delete_button)

        # Add CSV Import button
        self.csv_import_button = QPushButton("Import CSV")
        dml_layout.addRow(self.csv_import_button)
        layout.addLayout(dml_layout)

        # Add CSV Export button
        self.csv_export_button = QPushButton("Export CSV")
        dml_layout.addRow(self.csv_export_button)

        # Advanced Query
        query_layout = QVBoxLayout()
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your SQL query here...")
        self.execute_query_button = QPushButton("Execute Query")
        query_layout.addWidget(QLabel("Advanced Query:"))
        query_layout.addWidget(self.query_input)
        query_layout.addWidget(self.execute_query_button)
        layout.addLayout(query_layout)

        # Results
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)

        # Connect buttons
        self.create_table_button.clicked.connect(self.create_table)
        self.drop_table_button.clicked.connect(self.drop_table)
        self.insert_button.clicked.connect(self.open_insert_dialog)
        self.delete_button.clicked.connect(self.delete_data)
        self.table_select.currentIndexChanged.connect(self.on_table_selected)
        self.execute_query_button.clicked.connect(self.execute_advanced_query)
        self.csv_import_button.clicked.connect(self.import_csv)
        self.csv_export_button.clicked.connect(self.export_csv)

    def export_csv(self):
        table_name = self.table_select.currentText()
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table first.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            cursor = self.db.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            data = cursor.fetchall()
            # Get column names
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [column[0] for column in cursor.fetchall()]
            with open(file_path, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                # Write header
                csv_writer.writerow(columns)
                # Write data
                csv_writer.writerows(data)
            QMessageBox.information(self, "Success", f"Data exported successfully to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()

    def on_table_selected(self):
        table_name = self.table_select.currentText()
        if table_name:
            self.load_columns()
            self.display_last_100_rows(table_name)

    def display_last_100_rows(self, table_name):
        try:
            cursor = self.db.cursor()
            
            # Get the primary key column
            cursor.execute(f"SHOW KEYS FROM {table_name} WHERE Key_name = 'PRIMARY'")
            primary_key = cursor.fetchone()[4]  # Column name of the primary key
            
            # Fetch the last 100 rows
            query = f"SELECT * FROM {table_name} ORDER BY {primary_key} DESC LIMIT 100"
            cursor.execute(query)
            data = cursor.fetchall()
            
            self.results_table.setRowCount(len(data))
            self.results_table.setColumnCount(len(data[0]) if data else 0)
            
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    self.results_table.setItem(i, j, QTableWidgetItem(str(value)))
            
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            self.results_table.setHorizontalHeaderLabels([column[0] for column in columns])
            
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"Failed to display table data: {err}")
        finally:
            cursor.close()

    def import_csv(self):
        table_name = self.table_select.currentText()
        if not table_name:
            QMessageBox.warning(self, "Warning", "Please select a table first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                headers = next(csv_reader)  # Read the first row as headers

                cursor = self.db.cursor()
                
                # Get table columns
                cursor.execute(f"DESCRIBE {table_name}")
                table_columns = [column[0] for column in cursor.fetchall()]

                # Check if CSV headers match table columns
                if set(headers) != set(table_columns):
                    QMessageBox.critical(self, "Error", "CSV headers do not match table columns.")
                    return

                # Prepare the INSERT query
                columns = ', '.join(headers)
                placeholders = ', '.join(['%s'] * len(headers))
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

                # Insert data
                for row in csv_reader:
                    cursor.execute(query, row)

                self.db.commit()
                QMessageBox.information(self, "Success", "CSV data imported successfully.")
                self.display_table_data(table_name)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import CSV: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()

    def refresh_tables(self):
        cursor = self.db.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        self.table_select.clear()
        self.table_select.addItems([table[0] for table in tables])
        cursor.close()

    def create_table(self):
        table_name = self.table_name_input.text()
        if table_name:
            try:
                cursor = self.db.cursor()
                query = f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))"
                cursor.execute(query)
                self.db.commit()
                QMessageBox.information(self, "Success", f"Table {table_name} created successfully")
                self.refresh_tables()
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Error", f"Failed to create table: {err}")
            finally:
                cursor.close()

    def drop_table(self):
        table_name = self.table_name_input.text()
        if table_name:
            try:
                cursor = self.db.cursor()
                query = f"DROP TABLE {table_name}"
                cursor.execute(query)
                self.db.commit()
                QMessageBox.information(self, "Success", f"Table {table_name} dropped successfully")
                self.refresh_tables()
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Error", f"Failed to drop table: {err}")
            finally:
                cursor.close()

    def open_insert_dialog(self):
        table_name = self.table_select.currentText()
        if table_name:
            cursor = self.db.cursor()
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            cursor.close()

            dialog = InsertDialog(self, table_name, columns)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.insert_data(table_name, dialog.inputs)

    def insert_data(self, table_name, inputs):
        columns = ', '.join(inputs.keys())
        placeholders = ', '.join(['%s'] * len(inputs))
        values = tuple(inputs[key].text() for key in inputs)

        try:
            cursor = self.db.cursor()
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)
            self.db.commit()
            QMessageBox.information(self, "Success", "Data inserted successfully")
            self.display_table_data(table_name)
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"Failed to insert data: {err}")
        finally:
            cursor.close()

    def delete_data(self):
        table_name = self.table_select.currentText()
        column_name = self.column_select.currentText()
        value = self.value_input.text()
        if table_name and column_name and value:
            try:
                cursor = self.db.cursor()
                query = f"DELETE FROM {table_name} WHERE {column_name} = %s LIMIT 1"
                cursor.execute(query, (value,))
                self.db.commit()
                QMessageBox.information(self, "Success", "Data deleted successfully")
                self.display_table_data(table_name)
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Error", f"Failed to delete data: {err}")
            finally:
                cursor.close()

    def load_columns(self):
        table_name = self.table_select.currentText()
        if table_name:
            cursor = self.db.cursor()
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            self.column_select.clear()
            self.column_select.addItems([column[0] for column in columns])
            cursor.close()

    def display_table_data(self, table_name):
        try:
            cursor = self.db.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            data = cursor.fetchall()
            
            self.results_table.setRowCount(len(data))
            self.results_table.setColumnCount(len(data[0]) if data else 0)
            
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    self.results_table.setItem(i, j, QTableWidgetItem(str(value)))
            
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            self.results_table.setHorizontalHeaderLabels([column[0] for column in columns])
            
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"Failed to display table data: {err}")
        finally:
            cursor.close()

    def execute_advanced_query(self):
        query = self.query_input.toPlainText()
        if query:
            try:
                cursor = self.db.cursor()
                cursor.execute(query)
                
                # Fetch results
                results = cursor.fetchall()
                
                # Get column names
                column_names = [i[0] for i in cursor.description]
                
                # Display results in the table
                self.results_table.setRowCount(len(results))
                self.results_table.setColumnCount(len(column_names))
                self.results_table.setHorizontalHeaderLabels(column_names)
                
                for i, row in enumerate(results):
                    for j, value in enumerate(row):
                        self.results_table.setItem(i, j, QTableWidgetItem(str(value)))
                
                QMessageBox.information(self, "Success", "Query executed successfully")
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Error", f"Failed to execute query: {err}")
            finally:
                cursor.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())