# Premiere Cutter: FCPXML Generator for Adobe Premiere

`Premiere Cutter` is a Python application with a graphical user interface (GUI) that automates the creation of video editing projects for Adobe Premiere Pro. It takes a simple text-based "cut table" as input and generates a Final Cut Pro XML (`.xml`) file that defines a video sequence with cuts, transitions, and custom title cards.

This tool is designed to streamline the post-production workflow by allowing editors to define an entire edit decision list (EDL) in a plain text file, which the script then converts into a ready-to-import Premiere Pro project.

![GUI Screenshot](https://i.imgur.com/your-screenshot-url.png)  <!-- It's recommended to replace this with a real screenshot of your GUI -->

## What it Does

-   **Parses a Cut Table**: Reads a simple, human-readable text file that specifies the video files, timecodes for cuts, and descriptions for each segment.
-   **Generates Title Cards**: Automatically creates professional-looking title card images (`.png`) for your video. You can customize:
    -   Background color.
    -   Text content (or use the cut descriptions from your table).
    -   Placement (between cuts and/or at the beginning).
-   **Creates a Multi-Clip Timeline**: Assembles a video sequence with:
    -   Clips from multiple source video files.
    -   The generated title card images.
    -   Smooth cross-dissolve transitions between all elements.
-   **Generates a Premiere Pro XML File**: Outputs a `.xml` file that you can import directly into Adobe Premiere Pro, which will create the full timeline with all your cuts, title cards, and transitions.
-   **Handles Audio**: Correctly includes audio tracks from the source video files, preventing media linking issues in Premiere.
-   **Relative Paths**: Manages all file paths relative to the script's location, making the project portable.

## Usage

1.  **Prerequisites**:
    *   Python 3
    *   Pillow library: `pip install Pillow`
    *   Tkinter (usually included with Python; on Debian/Ubuntu, install with `sudo apt-get install python3-tk`)

2.  **Prepare your files**:
    *   Place `premierecutter.py` in your project folder.
    *   Ensure your source video files (e.g., `Video_Part_1.mp4`) are in the same folder.

3.  **Run the application**:
    ```bash
    python3 premierecutter.py
    ```

4.  **Use the GUI**:
    *   **Cut Table**: Paste the content of your cut table (like the provided `test_multi_source.txt`) into the main text box.
    *   **Title Card Options**: Customize the title cards using the checkboxes, color picker, and text field.
    *   **Generate XML**: Click this button. A file save dialog will appear, allowing you to name and save your `.xml` file.

5.  **Import into Premiere Pro**:
    *   Open Adobe Premiere Pro.
    *   Go to `File > Import...` and select the `.xml` file you just saved.
    *   Premiere will create a new sequence with your complete edit.

## Input File Format (`test_multi_source.txt`)

The script uses a specific format for the cut table. Here is an explanation based on the `test_multi_source.txt` example:

```
FILENAME: Multi_Source_Test_Project
# This is the name of your final project/sequence in Premiere.

SOURCE: Video_Part_1.mp4
# This specifies the first video file to use for the following cuts.

00:00:00-00:05:30,First segment of the first video
# Format: START_TIME-END_TIME,Description
# This creates a clip from 0s to 5m30s of Video_Part_1.mp4.
# The description is used for the title card text if the custom text field is empty.

00:07:00-00:12:15,Second segment of the first video

SOURCE: Video_Part_2.mp4
# Now, the script will use Video_Part_2.mp4 for the next set of cuts.

00:00:00-00:15:00,A long segment from the second video

SOURCE: Video_Part_3.mp4
# And so on...

00:00:00-00:02:30,Clip from the third video
```

This system allows you to create complex edits from multiple source files easily.

## File Structure

When you run `premierecutter.py`, it will create a subfolder for the generated title card images:

```
your_project_folder/
├── premierecutter.py
├── test_multi_source.txt
├── Video_Part_1.mp4
├── Video_Part_2.mp4
├── Your_Project_Name.xml      <-- Your output file
└── title_cards/                 <-- Generated title cards
    ├── title_card_1.png
    └── ...
```


