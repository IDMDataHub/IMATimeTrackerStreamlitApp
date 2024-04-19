
# IMATimeTrackerStreamlitApp

## Brief Description
**IMATimeTrackerStreamlitApp** is a suite of Streamlit applications designed to enhance time tracking and management in a professional environment. This suite includes two main applications tailored to the specific needs of employees and managers: `time_entry_online.py` for employees and `time_entry_manager_online.py` for managers. These tools provide an intuitive interface for time entry, project tracking, and feature advanced reporting and management functionalities.

### Features of `time_entry_online.py`
- **User Authentication**: Allows secure login for employees through an integrated authentication interface.
- **Time Entry and Modification**: Employees can easily enter and modify time spent on various projects or tasks.
- **Data Viewing and Editing**: Offers the ability to view time spent by week or year, with options to view and edit historical entries.
- **Integration with Cloud Storage**: Utilizes AWS S3 services for secure data storage and retrieval.

### Features of `time_entry_manager_online.py`
- **Management of ARCs and Study Information**: Enables managers to manage information related to clinical research assistants (ARCs) and ongoing studies.
- **Advanced Tracking and Data Visualization**: Provides a detailed view of time allocated to various projects, with charts and graphs for comprehensive tracking.
- **Detailed Dashboards**: Includes dashboards for each ARC and a general dashboard providing a complete overview.

## Getting Started
To launch an application, navigate to the directory containing the corresponding script and execute the appropriate command in your terminal:

For employees:
```bash
streamlit run time_entry_online.py
```

For managers:
```bash
streamlit run time_entry_manager_online.py
```

## Requirements
- Python 3.9 or newer.
- Python Libraries: `streamlit`, `pandas`, `datetime`, `locale`, `os`, `boto3`.

## Installation
1. Clone the repository or download the scripts.
2. Install the necessary dependencies using the command: `pip install streamlit pandas boto3`.
3. Launch the application following the instructions in the *Getting Started* section.

## Contribution
Contributions to **IMATimeTrackerStreamlitApp** are welcome. For any bug fixes, feature enhancements, or suggestions, feel free to open an issue or a pull request on the GitHub repository.
