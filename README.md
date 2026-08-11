# Singapore NRIC Barcode Generator

Live demo: https://hongyime.github.io/sgNRICgenerator65/

![Project screenshot](./screenshot.png)


This repository contains tools to generate barcodes for Singapore National Registration Identity Cards (NRIC). It includes both an interactive command-line application for offline generation and a web application for on-the-fly generation.

<p align="center">
  <img src="https://github.com/hongyime/sgNRIC2020/blob/main/static/NRIC.png" alt="NRIC Barcode Example" />
</p>

> **Disclaimer:**
> 1. USE AT OWN DISCRETION
> 2. FOR EDUCATIONAL PURPOSES ONLY

## Features
- **Web Application (`app.py`)**: A Flask-based web interface to generate and display an NRIC barcode instantly in your browser. (Does not save images to disk to avoid race conditions).
- **Offline CLI Generator (`cli.py`)**: A command-line tool that allows you to locally generate and save barcode `.png` files. You can choose to generate a barcode for a single NRIC, all combinations for a specific year, or all combinations for a range of years.

## Installation

1. Clone the repository and navigate into it.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Web Application (Flask)
To start the web server, run:
```bash
python app.py
```
Then, open your web browser and go to `http://localhost:5000`. You can enter an NRIC into the form and instantly see its barcode.

### 2. Offline CLI Generator
To use the offline interactive generator, run:
```bash
python cli.py
```
You will be prompted with an interactive menu:
1. **Generate for a specific NRIC**: Prompts you for a valid NRIC (e.g., `T0123456A`) and generates a single barcode image.
2. **Generate for a specific Year**: Generates barcode images for every valid NRIC starting with the provided year (e.g., `2000`).
3. **Generate for a Range of Years**: Generates barcode images for every valid NRIC across a range of years (e.g., `2000-2020`).

*Note: You will be asked where to save the files via an interactive prompt. Generating for a whole year can produce over 200,000 files!*

---

## Frequently Asked Questions

### What’s an NRIC/FIN number?
NRIC (National Registration Identity Card) is the identity document in use in Singapore. The NRIC number is a unique alpha-numeric serial number assigned to the document.

### What are NRIC/FIN numbers used for?
Many online voting, contests, giveaways, lucky draws, and account registrations on Singaporean websites require an NRIC number to participate.

### How is the barcode generated?
The barcode is generated using the `python-barcode` module (Code 39). However, to make it valid, the checksum (last character) when saving the image file is removed to prevent interference with the actual barcode. If a different NRIC is keyed in, the algorithm checks the validity based on the checksum character before generating.

### Is this legal?
The generation of NRIC numbers itself is legal, as the algorithm is made public. This codebase serves to demonstrate that it is possible to do so. However, you should not use the NRIC numbers to impersonate anyone as it is an offence. By using this tool to generate/copy NRIC/FIN numbers, you hereby agree to be responsible for your actions and waive all your rights to hold the author liable for any problems arising from your actions.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
