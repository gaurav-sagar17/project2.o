import mysql.connector
from datetime import datetime

# Define user roles and their permissions
# Define user roles and their permissions
PERMISSIONS = {
    'admin': {
        'add_series_with_cast', 'add_employee', 'assign_employee_to_series', 'add_grievance',
        'view_grievances', 'update_release_status', 'series_summary', 'find_employees_by_department',
        'update_series_budget', 'add_crew_member', 'view_series_cast_crew', 'search_series_by_genre',
        'view_series_by_production_firm', 'delete_series', 'delete_employee', 'delete_grievance',
        'delete_cast_member', 'delete_crew_member'  # Added delete permissions for admin
    },
    'hr': {
        'add_employee', 'view_grievances', 'find_employees_by_department', 'delete_employee',  # Added delete employee permission
    },
    'employee': {
        'view_grievances', 'series_summary', 'find_employees_by_department'
    },
    'normal user': {
        'series_summary', 'search_series_by_genre'
    }
}


# Set user role (will be prompted later)
USER_ROLE = ''

# Database connection function
def connect():
    return mysql.connector.connect(
        host='localhost',
        database='temp',
        user='root',
        password=''  # Use your database password
    )

# Permissions check decorator
def requires_permission(permission):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if permission in PERMISSIONS.get(USER_ROLE, set()):
                return func(*args, **kwargs)
            else:
                print(f"Access Denied: {USER_ROLE} does not have permission for this action.")
        return wrapper
    return decorator

# Define each function with the @requires_permission decorator


@requires_permission('add_series_with_cast')
def add_series_with_cast():
    series_name = input("Enter series name: ")
    reviews = input("Enter series reviews: ")
    budget = float(input("Enter series budget: "))
    genre = input("Enter genre type: ") 
    
    conn = connect()
    cursor = conn.cursor()

    # Insert the new series
    sql_series = """INSERT INTO Series (series_name, reviews, budget, genre_type)
                    VALUES (%s, %s, %s, %s)"""
    cursor.execute(sql_series, (series_name, reviews, budget, genre))
    series_id = cursor.lastrowid  # Get the ID of the newly added series

    # Adding initial cast members
    while True:
        add_cast = input("Do you want to add a cast member for this series? (y/n): ").strip().lower()
        if add_cast == 'n':
            break
        emp_id = int(input("Enter employee ID for cast member: "))
        num_of_episodes = int(input("Enter number of episodes: "))
        name_in_series = input("Enter character name in series: ")

        # Ensure you use the correct series_id from the inserted series
        sql_cast = """INSERT INTO Cast (emp_id, series_id, num_of_episodes, name_in_series) 
                      VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql_cast, (emp_id, series_id, num_of_episodes, name_in_series))

    conn.commit()
    print(f"Series '{series_name}' added successfully with initial cast members.")
    conn.close()


@requires_permission('add_employee')
def add_employee():
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    middle_name = input("Enter middle name (optional): ") or None
    dob = input("Enter date of birth (yyyy-mm-dd): ")
    department_id = int(input("Enter department ID: "))

    conn = connect()
    cursor = conn.cursor()

    # Insert employee (without specifying emp_id)
    sql = """INSERT INTO Employees (first_name, last_name, middle_name, DOB, department_id)
             VALUES (%s, %s, %s, %s, %s)"""
    cursor.execute(sql, (first_name, last_name, middle_name, dob, department_id))
    conn.commit()
    print(f"Employee '{first_name} {last_name}' added successfully.")
    conn.close()


@requires_permission('assign_employee_to_series')
def assign_employee_to_series():
    emp_id = int(input("Enter employee ID: "))
    series_id = int(input("Enter series ID to assign: "))

    conn = connect()
    cursor = conn.cursor()
    sql = "UPDATE Employees SET Series_Id = %s WHERE emp_id = %s"
    cursor.execute(sql, (series_id, emp_id))
    conn.commit()
    print(f"Employee ID {emp_id} assigned to Series ID {series_id}.")
    conn.close()

@requires_permission('add_grievance')
def add_grievance():
    emp_id = int(input("Enter employee ID: "))
    
    # Check if the employee exists
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id FROM Employees WHERE emp_id = %s", (emp_id,))
    employee = cursor.fetchone()
    
    if not employee:
        print(f"Error: Employee with ID {emp_id} does not exist.")
        conn.close()
        return  # Exit the function if employee does not exist
    
    grievance_text = input("Enter grievance text: ")

    # Insert the grievance if employee exists
    sql = """INSERT INTO Grievances (emp_id, grievances_text)
             VALUES (%s, %s)"""
    cursor.execute(sql, (emp_id, grievance_text))
    conn.commit()
    print(f"Grievance added for Employee ID {emp_id}.")
    conn.close()


@requires_permission('view_grievances')
def view_grievances():
    conn = connect()
    cursor = conn.cursor()
    
    # Fetch grievances data
    sql = """SELECT g.grievance_id, g.emp_id, e.first_name, e.last_name, g.grievances_text
             FROM Grievances g
             JOIN Employees e ON g.emp_id = e.emp_id"""
    cursor.execute(sql)
    grievances = cursor.fetchall()

    print("Grievances List:")
    if grievances:
        for grievance in grievances:
            print(f"Grievance ID: {grievance[0]}, Employee: {grievance[2]} {grievance[3]}, Grievance: {grievance[4]}")
    else:
        print("No grievances found.")
    
    conn.close()

@requires_permission('update_release_status')
def update_release_status():
    try:
        series_id = int(input("Enter series ID: "))
        platform = input("Enter platform name (e.g., Netflix, HBO): ").strip()
        release_date = input("Enter release date (yyyy-mm-dd): ").strip()

        # Ensure release_date is valid
        try:
            release_date = datetime.strptime(release_date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Please use yyyy-mm-dd format.")
            return

        conn = connect()
        cursor = conn.cursor()

        # Check if the series_id exists in the Series table
        cursor.execute("SELECT COUNT(*) FROM Series WHERE Series_Id = %s", (series_id,))
        if cursor.fetchone()[0] == 0:
            print(f"Series ID {series_id} does not exist.")
            return

        # Update the release status or insert a new record if it doesn't exist
        cursor.execute("""SELECT release_group_id FROM ReleaseGroups WHERE series_id = %s""", (series_id,))
        release_group = cursor.fetchone()

        if release_group:  # If the series already has a release record, update it
            release_id = release_group[0]
            sql_update = """UPDATE ReleaseGroups
                            SET platform = %s, release_date = %s
                            WHERE release_group_id = %s"""
            cursor.execute(sql_update, (platform, release_date, release_id))
            print(f"Release status updated for Series ID {series_id} on {platform} at {release_date}.")
        else:  # Insert a new release record if not exists
            sql_insert = """INSERT INTO ReleaseGroups (seriesId, platform, release_date)
                            VALUES (%s, %s, %s)"""
            cursor.execute(sql_insert, (series_id, platform, release_date))
            print(f"Release scheduled for Series ID {series_id} on {platform} at {release_date}.")

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        conn.close()

@requires_permission('series_summary')
def series_summary():
    conn = connect()
    cursor = conn.cursor()
    sql = """SELECT Series.Series_Id, Series.Series_Name, Productions.production_firm, Series.Budget
             FROM Series
             INNER JOIN Productions ON Series.production_id = Productions.production_id"""
    cursor.execute(sql)
    series = cursor.fetchall()
    print("Series Summary:")
    for s in series:
        print(f"Series ID: {s[0]}, Name: {s[1]}, Production Firm: {s[2]}, Budget: {s[3]}")
    conn.close()

@requires_permission('find_employees_by_department')
def find_employees_by_department():
    department_id = int(input("Enter department ID: "))
    conn = connect()
    cursor = conn.cursor()
    sql = """SELECT emp_id, first_name, last_name
             FROM Employees
             WHERE department_id = %s"""
    cursor.execute(sql, (department_id,))
    employees = cursor.fetchall()
    print(f"Employees in Department ID {department_id}:")
    for emp in employees:
        print(f"ID: {emp[0]}, Name: {emp[1]} {emp[2]}")
    conn.close()

@requires_permission('update_series_budget')
def update_series_budget():
    series_id = int(input("Enter series ID: "))
    new_budget = float(input("Enter new budget: "))
    
    conn = connect()
    cursor = conn.cursor()
    sql = "UPDATE Series SET Budget = %s WHERE Series_Id = %s"
    cursor.execute(sql, (new_budget, series_id))
    conn.commit()
    print(f"Series ID {series_id} budget updated to {new_budget}.")
    conn.close()

@requires_permission('add_crew_member')
def add_crew_member():
    emp_id = int(input("Enter employee ID for crew member: "))
    contract_duration = int(input("Enter contract duration in months: "))
    designation = input("Enter crew member designation (e.g., Director, Producer): ")
    series_id = int(input("Enter the series ID to associate with the crew member: "))  # New input for series_id

    conn = connect()
    cursor = conn.cursor()

    # Insert the new crew member into the CrewMembers table with series_id
    sql = """INSERT INTO CrewMembers (emp_id, contract_duration, designation, series_id)
             VALUES (%s, %s, %s, %s)"""
    cursor.execute(sql, (emp_id, contract_duration, designation, series_id))

    conn.commit()
    print(f"Crew member with Employee ID {emp_id} added successfully as '{designation}' to Series ID {series_id}.")
    conn.close()

@requires_permission('view_series_cast_crew')
def view_series_cast_crew():
    series_id = int(input("Enter series ID: "))

    conn = connect()
    cursor = conn.cursor()

    # View cast members
    print("\n--- Cast Members ---")
    sql_cast = """
        SELECT c.cast_id, e.first_name, e.last_name, c.name_in_series, c.num_of_episodes
        FROM Cast c
        JOIN Employees e ON c.emp_id = e.emp_id
        WHERE c.series_id = %s
    """
    cursor.execute(sql_cast, (series_id,))
    cast_members = cursor.fetchall()
    
    if cast_members:
        for cast in cast_members:
            print(f"ID: {cast[0]}, Name: {cast[1]} {cast[2]}, Character: {cast[3]}, Episodes: {cast[4]}")
    else:
        print("No cast members found for this series.")

    # View crew members
    print("\n--- Crew Members ---")
    sql_crew = """
        SELECT cr.crew_member_id, e.first_name, e.last_name, cr.designation, cr.contract_duration
        FROM CrewMembers cr
        JOIN Employees e ON cr.emp_id = e.emp_id
        WHERE cr.series_id = %s
    """
    cursor.execute(sql_crew, (series_id,))
    crew_members = cursor.fetchall()

    if crew_members:
        for crew in crew_members:
            print(f"ID: {crew[0]}, Name: {crew[1]} {crew[2]}, Designation: {crew[3]}, Contract Duration: {crew[4]} months")
    else:
        print("No crew members found for this series.")
    
    conn.close()


@requires_permission('search_series_by_genre')
def search_series_by_genre():
    genre = input("Enter genre to search for (e.g., Fantasy, Drama): ")
    conn = connect()
    cursor = conn.cursor()
    # Using LOWER to handle case-insensitive search
    sql = """SELECT Series_Id, Series_Name, Budget, Reviews
             FROM Series
             WHERE genre_type = LOWER(%s)"""
    cursor.execute(sql, (genre,))
    series = cursor.fetchall()
    
    if series:
        print(f"Series under genre '{genre}':")
        for s in series:
            print(f"ID: {s[0]}, Name: {s[1]}, Budget: {s[2]}, Reviews: {s[3]}")
    else:
        print(f"No series found under genre '{genre}'.")
    
    conn.close()


@requires_permission('view_series_by_production_firm')
def view_series_by_production_firm():
    production_firm = input("Enter production firm name: ")
    conn = connect()
    cursor = conn.cursor()
    sql = """SELECT s.Series_Id, s.Series_Name, s.Budget, s.genre_type
             FROM Series s
             JOIN Productions p ON s.production_id = p.production_id
             WHERE p.production_firm = %s"""
    cursor.execute(sql, (production_firm,))
    series = cursor.fetchall()
    print(f"Series produced by '{production_firm}':")
    for s in series:
        print(f"ID: {s[0]}, Name: {s[1]}, Budget: {s[2]}, Genre: {s[3]}")
    conn.close()

@requires_permission('delete_crew_member')
def delete_crew_member():
    crew_member_id = int(input("Enter the crew member ID to delete: "))

    conn = connect()
    cursor = conn.cursor()

    sql = "DELETE FROM CrewMembers WHERE crew_member_id = %s"
    cursor.execute(sql, (crew_member_id,))
    conn.commit()

    print(f"Crew member ID {crew_member_id} deleted successfully.")
    conn.close()

@requires_permission('delete_cast_member')
def delete_cast_member():
    cast_id = int(input("Enter the cast member ID to delete: "))

    conn = connect()
    cursor = conn.cursor()

    sql = "DELETE FROM Cast WHERE cast_id = %s"
    cursor.execute(sql, (cast_id,))
    conn.commit()

    print(f"Cast member ID {cast_id} deleted successfully.")
    conn.close()
@requires_permission('delete_grievance')
def delete_grievance():
    grievance_id = int(input("Enter the grievance ID to delete: "))

    conn = connect()
    cursor = conn.cursor()

    sql = "DELETE FROM Grievances WHERE grievance_id = %s"
    cursor.execute(sql, (grievance_id,))
    conn.commit()

    print(f"Grievance ID {grievance_id} deleted successfully.")
    conn.close()
@requires_permission('delete_employee')
def delete_employee():
    emp_id = int(input("Enter the employee ID to delete: "))

    conn = connect()
    cursor = conn.cursor()

    sql = "DELETE FROM Employees WHERE emp_id = %s"
    cursor.execute(sql, (emp_id,))
    conn.commit()

    print(f"Employee ID {emp_id} deleted successfully.")
    conn.close()
@requires_permission('delete_series')
def delete_series():
    series_id = int(input("Enter the series ID to delete: "))

    conn = connect()
    cursor = conn.cursor()

    sql = "DELETE FROM Series WHERE Series_Id = %s"
    cursor.execute(sql, (series_id,))
    conn.commit()

    print(f"Series ID {series_id} deleted successfully.")
    conn.close()

def show_menu():
    print("\nProduction Media Management System")
    print("1. Add a new series with initial cast")
    print("2. Add a new employee")
    print("3. Assign an employee to a series")
    print("4. Add an employee grievance")
    print("5. View all grievances")
    print("6. Schedule or update a series release")
    print("7. Show series summary")
    print("8. Find employees by department")
    print("9. Update a series budget")
    print("10. Add crew member to a series")
    print("11. View full cast and crew of a series")
    print("12. Search series by genre")
    print("13. View all series by production firm")
    print("14. Delete a series")            # New option
    print("15. Delete an employee")         # New option
    print("16. Delete a grievance")         # New option
    print("17. Delete a cast member")       # New option
    print("18. Delete a crew member")       # New option
    print("0. Exit")


def main():
    global USER_ROLE
    USER_ROLE = input("Enter your role (Admin, HR, Employee, Normal User): ").strip().lower()
    
    if USER_ROLE not in PERMISSIONS:
        print("Invalid role entered. Exiting system.")
        return

    while True:
        show_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            add_series_with_cast()
        elif choice == '2':
            add_employee()
        elif choice == '3':
            assign_employee_to_series()
        elif choice == '4':
            add_grievance()
        elif choice == '5':
            view_grievances()
        elif choice == '6':
            update_release_status()
        elif choice == '7':
            series_summary()
        elif choice == '8':
            find_employees_by_department()
        elif choice == '9':
            update_series_budget()
        elif choice == '10':
            add_crew_member()
        elif choice == '11':
            view_series_cast_crew()
        elif choice == '12':
            search_series_by_genre()
        elif choice == '13':
            view_series_by_production_firm()
        elif choice == '14':
            delete_series()  # New deletion option
        elif choice == '15':
            delete_employee()  # New deletion option
        elif choice == '16':
            delete_grievance()  # New deletion option
        elif choice == '17':
            delete_cast_member()  # New deletion option
        elif choice == '18':
            delete_crew_member()  # New deletion option
        elif choice == '0':
            print("Exiting the system. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")



main() 
### solve option 10 and 11 
