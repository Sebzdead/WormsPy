import pandas as pd
import seaborn as sns
import os
import matplotlib.pyplot as plt

# Specify the path to your WormsPy recoridng folder
directory = r'd:\WormSpy_video\test2_13-05-2024_16-08-30'
# Find the first .csv file in the directory
csv_file = next((file for file in os.listdir(directory) if file.endswith('.csv')), None)

# Check if a .csv file was found
if csv_file:
    # Construct the file path
    csv_file_path = os.path.join(directory, csv_file)
else:
    # Handle the case when no .csv file was found
    print("No .csv file found in the directory")
    # You can choose to exit the program or handle the error in a different way
    exit()

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(csv_file_path)

# Multiply all values in columns X and Y by 47.6249 to convert to nanometers
df['X'] = df['X'] * 47.6249
df['Y'] = df['Y'] * 47.6249

# Round all values in columns X and Y
df['X'] = df['X'].round()
df['Y'] = df['Y'].round()

# Convert to micrometers
df['X'] = df['X'] / 1000
df['Y'] = df['Y'] / 1000

# Create a new column called X or Y_vector that keeps a running total of X and Y
df['X_vector (um)'] = df['X'].cumsum()
df['Y_vector (um)'] = df['Y'].cumsum()

# Create a time column that is synced to frame count
df['Time'] = df.index / 10

# Save the DataFrame as a CSV file with the title "wormTrace.csv" in the specified directory
df.to_csv(os.path.join(directory, 'wormTrace.csv'), index=False)

# Create a scatter plot with X_vector (um) and Y_vector (um)
sns.scatterplot(data=df, x='X_vector (um)', y='Y_vector (um)', hue='Time')

# Save the plot as a PNG file
plt.savefig(os.path.join(directory, 'wormTrace.png'))

# Display the plot
plt.show()