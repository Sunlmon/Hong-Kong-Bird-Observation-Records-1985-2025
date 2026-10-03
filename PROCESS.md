# Process

## 1. Starting the Project Independently

Before starting Assignment 2, I read the assignment requirements and the Week 03 examples. I also ran the course template to understand the basic project structure.

At the beginning, I did not immediately change the visual style. I first tried to understand the basic workflow of the project.

One important step was learning the difference between `fetch.py` and `plot.py`.

`fetch.py` is responsible for downloading data from an external source and saving the original data locally.

`plot.py` reads the cached local data and transforms it into visual output.

This distinction was important because the assignment requires both a final visualisation and unchanged cached raw data. The project must also be able to run from local files after the data has been downloaded.

I chose Hong Kong bird observation records as my topic because I am interested in birds. I selected GBIF as the public data source.

For the visual direction, I did not want the final work to be only a standard scatter plot. I wanted the visual form to connect directly to the topic of birds. Therefore, I chose feathers to represent bird observation records.

## 2. Learning Step by Step with AI

After deciding on the basic direction, I used ChatGPT as a learning and discussion tool.

I did not begin by asking AI to complete the entire project. Instead, I started with questions about concepts that I did not understand.

For example, I asked about the meaning of different API URL parameters. I also asked why raw JSON data needed to be saved locally and what information was contained inside the JSON files.

After understanding these basic ideas, I continued learning how longitude and latitude are used.

Each GBIF bird record contains geographic information. The program needs to read the longitude and latitude values, then convert real geographic coordinates into screen positions in the web page.

This process also helped me understand loops and functions.

The dataset contains many bird records. It would not be practical to write separate code for every record. Instead, the program uses loops to read multiple records and functions to process each record.

These functions read information such as bird species, longitude, and latitude. The program then converts this information into visual elements.

As the project developed, I asked more specific questions. For example, I discussed how to add Hong Kong administrative boundaries and how to keep the same colour for the same bird species across different years.

Later, I continued refining the year selection function, feather drawing method, colour hierarchy, transparency, and glow effects.

Therefore, AI helped me first understand the data, then process coordinates, and finally improve the interaction and visual system.

## 3. Suggestions I Kept

### Separate raw GBIF JSON files for each year

I kept the suggestion to save one independent raw GBIF JSON file for each year.

The final files use this naming format:

```text
data/gbif-hong-kong-birds-YEAR.json
```

This format clearly separates the raw API responses for every year from 1985 to 2025.

It also follows the course requirement to cache unchanged source data. After downloading is complete, the program can read these local JSON files without visiting the API again.

### Caching the Hong Kong boundary locally

I also kept the suggestion to save the Hong Kong administrative boundary data locally.

The boundary file is saved as:

```text
data/hong-kong-boundary.geojson
```

If the bird data could be read offline but the map boundary still required an internet connection, the project would not be fully reproducible offline.

Therefore, both the bird data and the map boundary are saved in the `data/` folder. This allows the project to use one consistent local-data workflow.

### Using a fixed species colour table

I kept the suggestion that the same bird species should keep the same colour across different years.

If colours were randomly assigned again every year, the same species could appear in completely different colours. This would make comparison between years more difficult.

The final design identifies the 24 species with the most records across the full time period. Each species receives one fixed base hue, and this colour relationship remains unchanged when users select a different year.

### Using real geographic coordinates for feather positions

I also kept the suggestion to use real longitude and latitude to position the feathers.

Although the feathers are artistic visual forms, they still represent real observation records. I did not want to move feathers randomly just to make the composition look more even.

The program reads longitude and latitude from the GBIF data and converts these coordinates into positions in the visualisation. This preserves the spatial relationships in the original data.

## 4. Suggestions I Rejected

### Describing the project as a map of total bird population

I rejected the idea of describing the work as a map of bird population size or bird population density in Hong Kong.

GBIF provides occurrence records. These records show that a bird was observed, recorded, and published in the database. They do not directly show how many birds actually live in a location.

A place with more records may have more birdwatchers, easier access, more observation activity, or more active data publishers. In addition, this project requests a maximum of 300 records per year, so it uses a limited sample.

Therefore, I describe the project as a visualisation of Hong Kong bird observation records. I believe this is more accurate and better reflects what the data can support.

### Applying the same glow effect to every feather

I also rejected the idea of giving every feather the same glow effect.

If every feather glowed, the image would become very bright, but the visual hierarchy would become weaker. Users would find it harder to distinguish focal species from other species.

In the final design, only focal species with more records in the selected year have a soft, low-opacity glow. Other species use low-saturation blue-grey colours and do not glow.

The program also draws low-saturation feathers first and high-saturation feathers afterwards. This allows the brighter focal species to remain more visible in the upper visual layer.

I think this approach is clearer because visual emphasis should come from differences, rather than giving every element the same emphasis.

## 5. Final Development

After multiple adjustments, the project developed from an initial display of data points into an interactive visual system.

The final work uses a deep blue-black background.

Hong Kong administrative boundaries are placed on the lowest layer and drawn as thin grey lines. They provide a basic geographic reference.

Bird observation records are drawn as feathers. Each feather contains a curved shaft and branching barbs.

Different bird species use fixed base colours. Focal species use higher colour saturation and soft glow effects.

The feathers have a slow breathing animation. However, the animation does not change their original geographic positions.

The interactive web page includes a year selector for 1985–2025. Users can use this selector to explore data from different years.

The final project outputs include:

```text
site/index.html
```

and a static preview image for the README:

```text
out/hong-kong-bird-records-2025.svg
```

In this assignment, AI mainly helped me understand code and data concepts. AI also helped me discuss different implementation methods and refine visual and interaction details.

However, I chose the project topic, data source, and main visual direction myself. I also decided which suggestions to keep and which suggestions to reject.

Through this process, I did not only create a data visualisation. I also gained a better understanding of the workflow of a data project, including raw data collection, local caching, data reading, coordinate conversion, visual encoding, and interactive presentation.