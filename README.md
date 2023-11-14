---

# `Manga Lookup Tool`

## `Features`

- **Manga Search**: `Search for manga titles based on a query name.`
- **Description Retrieval**: `Retrieve detailed descriptions for specific manga titles.`
- **Chapter Information**: `Get information about the chapters of a particular manga.`
- **Cosine Similarity Search**: `Perform a similarity search based on a user query and previously retrieved manga titles.`

## `Dependencies`

Make sure to install the required Python packages using the following command:

```bash
pip install requests dataclasses scikit-learn beautifulsoup4
```

## `Usage`

1. Clone the repository:

```bash
git clone https://github.com/alluding/manga.git
```

2. Navigate to the project directory:

```bash
cd manga
```

3. Run the script:

```bash
python search.py
```

## `Example`

```python
query_name = "demon"
search_results = MangaSearch.search_manga(query_name)

if search_results:
    print("Search Results:")
    for result in search_results:
        print(f"{result.title} - {result.url} ({result.type})")
```

## `Contributing`

Feel free to contribute by opening issues or creating pull requests.

## `License`

This project is licensed under the [GNU General Public License](LICENSE).
