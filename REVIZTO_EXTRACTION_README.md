# Revizto Data Extraction Tracking

## Overview
The BIM Project Management system now includes comprehensive tracking of Revizto data extractions. This feature allows users to monitor when extractions were performed and what projects have changed since the last run.

## New Components

### Database Table: ReviztoExtractionRuns
- Tracks all Revizto data extraction runs
- Stores start/end times, status, and extraction statistics
- Includes export folder path and notes

### Database Functions
- `start_revizto_extraction_run()` - Records the start of an extraction
- `complete_revizto_extraction_run()` - Updates run with final statistics
- `get_revizto_extraction_runs()` - Retrieves extraction history
- `get_last_revizto_extraction_run()` - Gets the most recent completed run
- `get_revizto_projects_since_last_run()` - Shows projects changed since last extraction

### UI Components
- **Revizto Data** sub-tab in Review Management
- Extraction control buttons (Start Extract, Refresh History)
- Extraction history table showing run details
- Recent project changes table
- Last run status display

## Usage

1. Navigate to **Review Management** → **Revizto Data** tab
2. Click **"Start Revizto Extract"** to launch the ReviztoDataExporter.exe
3. The system automatically records the extraction run
4. Use **"Refresh History"** to update the display
5. View extraction history and project changes in the tables

## Features

- **Automatic Run Tracking**: Every extraction is logged with timestamps
- **Project Change Detection**: Shows which projects were modified since last extraction
- **Status Monitoring**: Tracks running, completed, and failed extractions
- **Statistics**: Displays counts of projects, issues, and licenses extracted
- **Export Folder Tracking**: Records where extracted data is stored

## Future Enhancements

- Automatic completion detection when export files are created
- Email notifications for extraction completion
- Integration with project scheduling
- Detailed change logs per project