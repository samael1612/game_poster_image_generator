sources = '''United Kingdom:Sky Sports F1 HD, Spain:DAZN F1 Spain, Germany:Sky Sport F1 HD Germany, Hungary:M4 Sport HU, Estonia:Viaplay EE, Lithuania:Viaplay LT, United States: Viaplay LT, Latvia:Viaplay LV, Iceland:Viaplay IS, United Kingdom:Viaplay IS, The Netherlands:Viaplay NL, United States: Sky Sport F1 HD Germany, Poland:Viaplay PL'''

# Normalize the string to handle inconsistent spaces
sources = sources.replace(' ,', ',').replace(' , ', ',').replace(': ', ':')  # Clean up spaces
sources_list = [source.strip() for source in sources.split(",")]  # Strip leading/trailing spaces after split

# Define a custom sorting function
def custom_sort(source):
    # Prioritize all United Kingdom and United States entries
    if source.startswith("United Kingdom"):
        return (0, source)
    elif source.startswith("United States"):
        return (1, source)
    # Sort all other sources alphabetically
    return (2, source)

# Sort the sources using the custom sort function
sources_list.sort(key=custom_sort)

# Output sorted sources
print(sources_list)
