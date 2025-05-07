# Web Scraping Project

This project is a web scraping tool designed to extract content from online news websites, including dynamic and modern sites. It follows links, extracts the content, and saves the data in `.csv` format for further analysis.

## Features

- Scrapes dynamic and modern websites.
- Follows links to extract related content.
- Converts and saves extracted data into `.csv` format.
- Utilizes powerful libraries for efficient and reliable scraping.

## Installation

To get started, clone the repository and install the required dependencies:

```bash
git clone https://github.com/sam4rano/scrapper.git
cd masakhane_project
pip install -r requirements.txt
```

Ensure you have the following dependencies installed:
- [pandas](https://pandas.pydata.org/)
- [playwright](https://playwright.dev/)
- [crawl4ai](https://github.com/sam4rano/crawl4ai)

## Usage

1. **Setup Playwright**: Run the following command to install the necessary browser binaries:
	```bash
	playwright install
	```

2. **Run the Scraper**: Execute the script to start scraping:
	```bash
	python scraper.py
	```

3. **Output**: The scraped data will be saved in a `.csv` file in the output directory.

## Contribution Guidelines

We welcome contributions to improve this project! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
	```bash
	git checkout -b feature-name
	```
3. Commit your changes:
	```bash
	git commit -m "Add feature-name"
	```
4. Push to your branch:
	```bash
	git push origin feature-name
	```
5. Open a pull request.

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

Special thanks to the developers of `pandas`, `playwright`, and `crawl4ai` for their amazing tools that made this project possible.