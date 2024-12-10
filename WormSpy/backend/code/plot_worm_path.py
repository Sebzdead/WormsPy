import matplotlib.pyplot as plt
import pandas as pd
import pathlib

def plot_worm_path(file_path: pathlib.Path, save_plot=True):
    """
    Create a scatter plot of worm path from CSV data.
    
    Args:
        file_path (str): Path to CSV file containing worm tracking data
        save_plot (bool): Whether to save the plot as PNG
        show_plot (bool): Whether to display the plot
    
    Returns:
        matplotlib.figure.Figure: The generated plot figure
    """
    # split the file path to get the directory and the file name
    file_directory = file_path.parents[0]
    csv_file_name = file_path.name.replace('.csv', '')
    
    # Read data
    df = pd.read_csv(file_path)

    # Create figure
    fig = plt.figure(figsize=(12, 8))

    # Create scatter plot with proper column names
    plt.scatter(df['X_motor'], df['Y_motor'], c='black', s=5)

    # Set limits
    plt.xlim(0, 50800)
    plt.ylim(0, 50800)

    # Labels and formatting
    plt.xlabel('Coordinates X (μm)')
    plt.ylabel('Coordinates Y (μm)')
    plt.title('Worm path for '+ f'{csv_file_name}', pad=20)
    plt.gca().set_facecolor('white')
    plt.grid(True, alpha=0.3)

    if save_plot:
        plt.savefig(f"{file_directory / csv_file_name}.png", 
                    dpi=300, 
                    bbox_inches='tight',
                    facecolor='white')