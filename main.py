from search_func import hoopla_search, zero_search, libby_search, search_all

def main():
    query_title = input("Enter the title to search for: ")
    query_author = input("Enter the author (optional, press Enter to skip): ")
    query_author = query_author if query_author else None

    search_all(query_title, query_author)

if __name__ == "__main__":
    main()
