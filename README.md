# Excel Dashboard - Automatic Chart Generator

A web application that automatically detects Excel file columns and generates dynamic charts without any manual configuration.

## Features

- **Automatic Column Detection**: Analyzes Excel files and automatically identifies column types (numeric, text, date, boolean)
- **Dynamic Chart Generation**: Creates appropriate charts based on data types:
  - Bar charts for numeric data
  - Pie charts for categorical data
  - Line charts for trend analysis
  - Scatter plots for correlations
- **Drag & Drop Interface**: Easy file upload with drag and drop support
- **Data Type Inference**: Smart detection of data types with sample values
- **Responsive Design**: Works on desktop and mobile devices

## Supported File Formats

- Excel files (.xlsx, .xls)
- CSV files (.csv)

## How to Use

1. Open `index.html` in a web browser
2. Drag and drop an Excel file onto the upload area or click to browse
3. The system will automatically:
   - Detect all columns and their data types
   - Display file information and column details
   - Generate appropriate charts based on the data

## Technical Implementation

### Column Detection Algorithm

The application uses intelligent data type inference:

1. **Numeric Detection**: Checks if 80%+ of values are valid numbers
2. **Date Detection**: Identifies common date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
3. **Boolean Detection**: Recognizes true/false, yes/no, 1/0 patterns
4. **Text Detection**: Default for all other data types

### Chart Generation Logic

- **Bar Charts**: Created for the first numeric column found
- **Pie Charts**: Generated for text columns with ≤10 unique values
- **Line Charts**: Compare up to 3 numeric columns for trend analysis
- **Scatter Plots**: Show relationships between two numeric columns

## Dependencies

- [Chart.js](https://www.chartjs.org/) - Chart rendering
- [SheetJS (xlsx)](https://sheetjs.com/) - Excel file parsing
- [Tailwind CSS](https://tailwindcss.com/) - Styling

## File Structure

```
excel-dashboard/
├── index.html          # Main HTML file
├── app.js             # Application logic
└── README.md          # Documentation
```

## Browser Compatibility

Works in all modern browsers that support:
- ES6 JavaScript
- Canvas API (for charts)
- File API (for file uploads)

## Example Use Cases

- **Sales Data**: Automatically generate revenue charts and product distribution
- **Survey Results**: Create pie charts for responses and bar charts for ratings
- **Financial Data**: Generate trend lines and scatter plots for analysis
- **Scientific Data**: Visualize experimental results without manual setup

## Privacy Notice

This application processes files entirely in your browser. No data is sent to external servers, ensuring complete privacy of your Excel files.
