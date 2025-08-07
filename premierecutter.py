#!/usr/bin/env python3
"""
Final Cut Pro XML Generator with Title Cards and Transitions - GUI Version
Generates XML files that can be imported into Adobe Premiere Pro
Based on the provided cut table format with Tkinter GUI
"""

import re
import os
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont

def timecode_to_frames(timecode, fps=30):
    """Convert MM:SS:FF or HH:MM:SS:FF timecode to frame number"""
    parts = timecode.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        frames = 0
    elif len(parts) == 4:
        hours, minutes, seconds, frames = map(int, parts)
    else:
        raise ValueError(f"Invalid timecode format: {timecode}")
    
    return (hours * 3600 + minutes * 60 + seconds) * fps + frames

def generate_uuid():
    """Generate a UUID for XML elements"""
    return str(uuid.uuid4())

def parse_cut_table(table_text):
    """Parse the cut table format into structured data"""
    lines = [line.strip() for line in table_text.strip().split("\n") if line.strip()]
    
    filename = None
    sources = {}
    current_source = None
    
    for line in lines:
        if line.startswith("FILENAME:"):
            filename = line.split("FILENAME:")[1].strip()
        elif line.startswith("SOURCE:"):
            current_source = line.split("SOURCE:")[1].strip()
            sources[current_source] = []
        elif current_source and "-" in line and "," in line:
            # Parse timecode range and label
            timecode_part, label = line.split(",", 1)
            start_time, end_time = timecode_part.split("-")
            sources[current_source].append({
                "start": start_time.strip(),
                "end": end_time.strip(),
                "label": label.strip()
            })
    
    return filename, sources

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip("#")
    lv = len(hex_color)
    return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def create_title_card_image(text, bg_color_hex, output_path, width=1920, height=1080):
    """Create a title card image with specified text and background color"""
    # Convert hex to RGB
    bg_color = hex_to_rgb(bg_color_hex)
    
    # Create image with background color
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Calculate frame box dimensions (8% from edges)
    margin = int(min(width, height) * 0.08)
    frame_left = margin
    frame_top = margin
    frame_right = width - margin
    frame_bottom = height - margin
    
    # Draw white frame box
    frame_thickness = 8
    draw.rectangle([frame_left, frame_top, frame_right, frame_bottom], 
                   outline="white", width=frame_thickness)
    
    # Try to load Arial font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except (OSError, IOError):
            font = ImageFont.load_default()
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate text position (centered)
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    # Draw text in white
    draw.text((text_x, text_y), text, fill="white", font=font)
    
    # Save image
    img.save(output_path, "PNG")
    print(f"Title card image created: {output_path}")

def create_title_card_xml(title_text, start_frame, duration_frames, clip_id, image_path):
    """Create XML for a title card as an image clip"""
    # Use the image_path for the title card
    title_xml = f"""
					<clipitem id="clipitem-{clip_id}">
						<masterclipid>masterclip-{clip_id}</masterclipid>
						<name>{os.path.basename(image_path)}</name>
						<enabled>TRUE</enabled>
						<duration>{duration_frames}</duration>
						<rate>
							<timebase>30</timebase>
							<ntsc>FALSE</ntsc>
						</rate>
						<start>{start_frame}</start>
						<end>{start_frame + duration_frames}</end>
						<in>0</in>
						<out>{duration_frames}</out>
						<alphatype>none</alphatype>
						<pixelaspectratio>square</pixelaspectratio>
						<anamorphic>FALSE</anamorphic>
						<file id="file-{clip_id}">
							<name>{os.path.basename(image_path)}</name>
							<pathurl>file://localhost/{os.path.abspath(image_path)}</pathurl>
							<rate>
								<timebase>30</timebase>
								<ntsc>FALSE</ntsc>
							</rate>
							<duration>{duration_frames}</duration>
							<timecode>
								<rate>
									<timebase>30</timebase>
									<ntsc>FALSE</ntsc>
								</rate>
								<string>00:00:00:00</string>
								<frame>0</frame>
								<displayformat>NDF</displayformat>
							</timecode>
							<media>
								<video>
									<samplecharacteristics>
										<rate>
											<timebase>30</timebase>
											<ntsc>FALSE</ntsc>
										</rate>
										<width>1920</width>
										<height>1080</height>
										<anamorphic>FALSE</anamorphic>
										<pixelaspectratio>square</pixelaspectratio>
										<fielddominance>none</fielddominance>
									</samplecharacteristics>
								</video>
							</media>
						</file>
					</clipitem>"""
    
    return title_xml

def create_transition_xml(start_frame, end_frame):
    """Create XML for a cross-dissolve transition"""
    transition_xml = f"""					<transitionitem>
						<start>{start_frame}</start>
						<end>{end_frame}</end>
						<alignment>center</alignment>
						<cutPointTicks>{start_frame * 254016000000 // 30}</cutPointTicks>
						<rate>
							<timebase>30</timebase>
							<ntsc>FALSE</ntsc>
						</rate>
						<effect>
							<name>Cross Dissolve</name>
							<effectid>Cross Dissolve</effectid>
							<effectcategory>Dissolve</effectcategory>
							<effecttype>transition</effecttype>
							<mediatype>video</mediatype>
							<wipecode>0</wipecode>
							<wipeaccuracy>100</wipeaccuracy>
							<startratio>0</startratio>
							<endratio>1</endratio>
							<reverse>FALSE</reverse>
						</effect>
					</transitionitem>"""
    
    return transition_xml

def generate_xml(filename, sources, include_title_cards=True, title_before_first=False, bg_color="#E96502", title_text="", title_card_images_dir="title_cards"):
    """Generate Final Cut Pro XML from cut data with title cards and transitions"""
    
    # Generate unique IDs
    project_uuid = generate_uuid()
    sequence_uuid = generate_uuid()
    
    # Build clip items for video track
    video_clips = []
    audio_clips = [] # New list for audio clips
    current_start = 0
    clip_id_counter = 4  # Start after masterclip IDs
    
    # Transition duration is 0.5 seconds (15 frames at 30fps)
    transition_duration = 15
    # Title card duration is 7 seconds (210 frames at 30fps)
    title_duration = 210
    
    # Ensure title card images directory exists relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_title_card_images_dir = os.path.join(script_dir, title_card_images_dir)
    os.makedirs(full_title_card_images_dir, exist_ok=True)

    # Dictionary to store unique file IDs and masterclip IDs for each source video
    source_file_ids = {}
    source_masterclip_ids = {}
    file_id_counter = 1

    # Add title card before first cut if requested
    if include_title_cards and title_before_first:
        card_text = title_text if title_text else "Intro Title"
        image_path = os.path.join(full_title_card_images_dir, f"title_card_{clip_id_counter}.png")
        create_title_card_image(card_text, bg_color, image_path)
        video_clips.append(create_title_card_xml(card_text, current_start, title_duration, clip_id_counter, image_path))
        current_start += title_duration
        clip_id_counter += 1
        
        # Add transition after initial title card
        transition_start = current_start - transition_duration // 2
        transition_end = current_start + transition_duration // 2
        video_clips.append(create_transition_xml(transition_start, transition_end))
    
    for source_file, cuts in sources.items():
        # Assign unique file and masterclip IDs for this source file if not already assigned
        if source_file not in source_file_ids:
            source_file_ids[source_file] = file_id_counter
            source_masterclip_ids[source_file] = file_id_counter # Using same counter for simplicity
            file_id_counter += 1

        current_file_id = source_file_ids[source_file]
        current_masterclip_id = source_masterclip_ids[source_file]

        for i, cut in enumerate(cuts):
            start_frames = timecode_to_frames(cut["start"])
            end_frames = timecode_to_frames(cut["end"])
            duration = end_frames - start_frames
            
            # Add video clip
            video_clips.append(f"""
					<clipitem id="clipitem-{clip_id_counter}">
						<masterclipid>masterclip-{current_masterclip_id}</masterclipid>
						<name>{source_file}</name>
						<enabled>TRUE</enabled>
						<duration>130554</duration>
						<rate>
							<timebase>30</timebase>
							<ntsc>FALSE</ntsc>
						</rate>
						<start>{current_start}</start>
						<end>{current_start + duration}</end>
						<in>{start_frames}</in>
						<out>{end_frames}</out>
						<alphatype>none</alphatype>
						<pixelaspectratio>square</pixelaspectratio>
						<anamorphic>FALSE</anamorphic>
						<file id="file-{current_file_id}">
							<name>{source_file}</name>
							<pathurl>file://localhost/{os.path.abspath(source_file)}</pathurl>
							<rate>
								<timebase>30</timebase>
								<ntsc>FALSE</ntsc>
							</rate>
							<duration>130554</duration>
							<timecode>
								<rate>
									<timebase>30</timebase>
									<ntsc>FALSE</ntsc>
								</rate>
								<string>00:00:00:00</string>
								<frame>0</frame>
								<displayformat>NDF</displayformat>
							</timecode>
							<media>
								<video>
									<samplecharacteristics>
										<rate>
											<timebase>30</timebase>
											<ntsc>FALSE</ntsc>
										</rate>
										<width>1920</width>
										<height>1080</height>
										<anamorphic>FALSE</anamorphic>
										<pixelaspectratio>square</pixelaspectratio>
										<fielddominance>none</fielddominance>
									</samplecharacteristics>
								</video>
								<audio>
									<samplecharacteristics>
										<depth>16</depth>
										<samplerate>44100</samplerate>
									</samplecharacteristics>
									<channelcount>2</channelcount>
								</audio>
							</media>
						</file>
					</clipitem>"""
            )
            
            # Add audio clip for each channel
            audio_clips.append(f"""
					<clipitem id="audio-clipitem-{clip_id_counter}">
						<masterclipid>masterclip-{current_masterclip_id}</masterclipid>
						<name>{source_file}</name>
						<enabled>TRUE</enabled>
						<duration>130554</duration>
						<rate>
							<timebase>30</timebase>
							<ntsc>FALSE</ntsc>
						</rate>
						<start>{current_start}</start>
						<end>{current_start + duration}</end>
						<in>{start_frames}</in>
						<out>{end_frames}</out>
						<file id="file-{current_file_id}"/>
						<sourcetrack>
							<mediatype>audio</mediatype>
							<trackindex>1</trackindex>
						</sourcetrack>
						<channelcount>2</channelcount>
					</clipitem>"""
            )

            audio_clips.append(f"""
					<clipitem id="audio-clipitem-{clip_id_counter}-2">
						<masterclipid>masterclip-{current_masterclip_id}</masterclipid>
						<name>{source_file}</name>
						<enabled>TRUE</enabled>
						<duration>130554</duration>
						<rate>
							<timebase>30</timebase>
							<ntsc>FALSE</ntsc>
						</rate>
						<start>{current_start}</start>
						<end>{current_start + duration}</end>
						<in>{start_frames}</in>
						<out>{end_frames}</out>
						<file id="file-{current_file_id}"/>
						<sourcetrack>
							<mediatype>audio</mediatype>
							<trackindex>2</trackindex>
						</sourcetrack>
						<channelcount>2</channelcount>
					</clipitem>"""
            )
            
            current_start += duration
            
            # Add transition before title card (except for the last clip)
            if include_title_cards and i < len(cuts) - 1:
                transition_start = current_start - transition_duration // 2
                transition_end = current_start + transition_duration // 2
                video_clips.append(create_transition_xml(transition_start, transition_end))
                
                # Add title card as image
                clip_id_counter += 1
                card_text = cut["label"] if not title_text else title_text
                image_path = os.path.join(full_title_card_images_dir, f"title_card_{clip_id_counter}.png")
                create_title_card_image(card_text, bg_color, image_path)
                video_clips.append(create_title_card_xml(card_text, current_start, title_duration, clip_id_counter, image_path))
                current_start += title_duration
                
                # Add transition after title card
                transition_start = current_start - transition_duration // 2
                transition_end = current_start + transition_duration // 2
                video_clips.append(create_transition_xml(transition_start, transition_end))
            
            clip_id_counter += 1
    
    total_frames = current_start
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
	<sequence id="sequence-1" explodedTracks="true">
		<uuid>{sequence_uuid}</uuid>
		<duration>{total_frames}</duration>
		<rate>
			<timebase>30</timebase>
			<ntsc>FALSE</ntsc>
		</rate>
		<name>{filename}</name>
		<media>
			<video>
				<format>
					<samplecharacteristics>
						<rate>
							<timebase>30</timebase>
							<ntsc>FALSE</ntsc>
						</rate>
						<codec>
							<name>Apple ProRes 422</name>
							<appspecificdata>
								<appname>Final Cut Pro</appname>
								<appmanufacturer>Apple Inc.</appmanufacturer>
								<appversion>7.0</appversion>
								<data>
									<qtcodec>
										<codecname>Apple ProRes 422</codecname>
										<codectypename>Apple ProRes 422</codectypename>
										<codectypecode>apcn</codectypecode>
										<codecvendorcode>appl</codecvendorcode>
										<spatialquality>1024</spatialquality>
										<temporalquality>0</temporalquality>
										<keyframerate>0</keyframerate>
										<datarate>0</datarate>
									</qtcodec>
								</data>
							</appspecificdata>
						</codec>
						<width>1920</width>
						<height>1080</height>
						<anamorphic>FALSE</anamorphic>
						<pixelaspectratio>square</pixelaspectratio>
						<fielddominance>none</fielddominance>
						<colordepth>24</colordepth>
					</samplecharacteristics>
				</format>
				<track>
{chr(10).join(video_clips)}
					<enabled>TRUE</enabled>
					<locked>FALSE</locked>
				</track>
			</video>
			<audio>
				<format>
					<samplecharacteristics>
						<depth>16</depth>
						<samplerate>44100</samplerate>
					</samplecharacteristics>
				</format>
				<track>
{chr(10).join(audio_clips)}
					<enabled>TRUE</enabled>
					<locked>FALSE</locked>
				</track>
			</audio>
		</media>
		<timecode>
			<rate>
				<timebase>30</timebase>
				<ntsc>FALSE</ntsc>
			</rate>
			<string>00:00:00:00</string>
			<frame>0</frame>
			<displayformat>NDF</displayformat>
		</timecode>
	</sequence>
</xmeml>"""
    
    return xml_content

class XMLGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Final Cut Pro XML Generator")
        self.root.geometry("800x700")
        
        # Variables
        self.include_title_cards = tk.BooleanVar(value=True)
        self.title_before_first = tk.BooleanVar(value=False)
        self.bg_color = tk.StringVar(value="#E96502")
        self.title_text = tk.StringVar(value="")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Final Cut Pro XML Generator", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Cut table input
        ttk.Label(main_frame, text="Cut Table:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.cut_table_text = scrolledtext.ScrolledText(main_frame, width=80, height=15)
        self.cut_table_text.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Title Card Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Title card toggle
        ttk.Checkbutton(options_frame, text="Include Title Cards", variable=self.include_title_cards).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Title before first cut
        ttk.Checkbutton(options_frame, text="Title Card Before First Cut", variable=self.title_before_first).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Background color
        color_frame = ttk.Frame(options_frame)
        color_frame.grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(color_frame, text="Background Color:").pack(side=tk.LEFT)
        self.color_button = tk.Button(color_frame, text="Choose Color", command=self.choose_color, bg=self.bg_color.get())
        self.color_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Title text
        ttk.Label(options_frame, text="Title Text (leave empty to use cut labels):").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Entry(options_frame, textvariable=self.title_text, width=50).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Generate button
        ttk.Button(buttons_frame, text="Generate XML", command=self.generate_xml_file).pack(side=tk.LEFT, padx=(0, 10))
        
        # Load example button
        ttk.Button(buttons_frame, text="Load Example", command=self.load_example).pack(side=tk.LEFT)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def choose_color(self):
        color = colorchooser.askcolor(title="Choose Background Color", color=self.bg_color.get())
        if color[1]:  # If a color was selected
            self.bg_color.set(color[1])
            self.color_button.config(bg=color[1])
    
    def load_example(self):
        example_text = """FILENAME: Multi_Source_Test_Project
SOURCE: Video_Part_1.mp4
00:00:00-00:05:30,Introduction and Overview
00:07:00-00:12:15,Key Concepts Explained
00:15:30-00:20:45,First Case Study
SOURCE: Video_Part_2.mp4
00:00:00-00:08:20,Advanced Techniques
00:10:00-00:15:30,Implementation Examples
00:18:00-00:22:45,Best Practices
SOURCE: Video_Part_3.mp4
00:02:15-00:07:30,Real-world Applications
00:09:45-00:14:20,Troubleshooting Guide
00:16:00-00:19:30,Conclusion and Next Steps"""
        
        self.cut_table_text.delete(1.0, tk.END)
        self.cut_table_text.insert(1.0, example_text)
    
    def generate_xml_file(self):
        table_text = self.cut_table_text.get(1.0, tk.END).strip()
        
        if not table_text:
            messagebox.showerror("Error", "Please enter a cut table.")
            return
        
        try:
            # Parse the cut table
            filename, sources = parse_cut_table(table_text)
            
            if not filename or not sources:
                messagebox.showerror("Error", "Could not parse the cut table. Please check the format.")
                return
            
            # Generate XML
            xml_content = generate_xml(
                filename, 
                sources, 
                include_title_cards=self.include_title_cards.get(),
                title_before_first=self.title_before_first.get(),
                bg_color=self.bg_color.get(),
                title_text=self.title_text.get()
            )
            
            # Save to file
            output_filename = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
                initialfile=f"{filename}.xml"
            )
            
            if output_filename:
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                
                messagebox.showinfo("Success", f"XML file generated successfully:\n{output_filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating XML: {e}")

def main():
    root = tk.Tk()
    app = XMLGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

