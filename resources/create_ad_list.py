import requests
import os
import re  # Import de la bibliothèque pour les expressions régulières

# URL de la liste qui contient toutes les autres listes de blocage
MAIN_URL_LIST = "https://raw.githubusercontent.com/hl2guide/All-in-One-Customized-Adblock-List/master/adfilters_urls.txt"

# Nom du fichier de sortie
OUTPUT_FILE = "ad_block_list.txt"

# Expression régulière pour valider un nom de domaine.
# C'est un modèle qui vérifie si une chaîne de caractères ressemble à un domaine valide.
HOSTNAME_REGEX = re.compile(
    r"^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


def is_valid_hostname(hostname: str) -> bool:
    """Vérifie si une chaîne est un nom de domaine valide à l'aide d'une regex."""
    if not hostname or len(hostname) > 255:
        return False
    # La méthode .match() vérifie si le début de la chaîne correspond au modèle.
    return HOSTNAME_REGEX.match(hostname) is not None


def parse_line(line: str) -> list[str] | None:
    """
    Analyse une ligne d'un fichier de blocage pour en extraire une liste de noms de domaine valides.
    """
    line = line.strip()

    # Ignore les commentaires, les lignes vides, les whitelists et les filtres cosmétiques
    if not line or line.startswith(("!", "@@", "[", "#", "##")):
        return None

    # Nettoie les guillemets et apostrophes qui pourraient entourer la ligne
    line = line.strip("'\"")

    found_domains = []

    if "domain=" in line:
        try:
            domains_part = line.split("domain=")[1]
            potential_domains = domains_part.split("|")

            for domain in potential_domains:
                if domain.startswith("~"):
                    continue
                cleaned_domain = (
                    domain.strip().lower()
                )  # Met en minuscule pour la validation
                if is_valid_hostname(cleaned_domain):
                    found_domains.append(cleaned_domain)
            return found_domains if found_domains else None
        except IndexError:
            pass

    if " " in line or "\t" in line:
        parts = line.split()
        line = parts[-1]

    if "$" in line:
        line = line.split("$")[0]

    line = (
        line.replace("||", "")
        .replace("^", "")
        .replace("www.", "")
        .strip(",")
        .strip()
        .lower()
    )

    # Validation finale avec la regex
    if is_valid_hostname(line):
        return [line]

    return None


def generate_blocklist():
    """
    Fonction principale pour générer la liste de blocage complète.
    """
    print(
        "Démarrage de la création de la liste de blocage (version avec validation)..."
    )

    final_domains = set()

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )

    try:
        print(f"Téléchargement de la liste principale depuis {MAIN_URL_LIST}")
        response = session.get(MAIN_URL_LIST, timeout=10)
        response.raise_for_status()
        blocklist_urls = response.text.splitlines()
        print(f"Trouvé {len(blocklist_urls)} listes de filtres à traiter.\n")

    except requests.RequestException as e:
        print(f"Erreur: Impossible de télécharger la liste principale d'URLs : {e}")
        return

    for url in blocklist_urls:
        url = url.strip()
        if not url or url.startswith("#"):
            continue

        print(f"Traitement de la liste : {url}")
        try:
            list_response = session.get(url, timeout=15)
            if list_response.status_code != 200:
                print(
                    f"  -> Avertissement : Échec du téléchargement (code: {list_response.status_code})"
                )
                continue

            content = list_response.text
            count_before = len(final_domains)

            for line in content.splitlines():
                domains_from_line = parse_line(line)
                if domains_from_line:
                    final_domains.update(domains_from_line)

            added_count = len(final_domains) - count_before
            print(f"  -> Ajout de {added_count} nouveaux domaines valides.")

        except requests.RequestException as e:
            print(f"  -> Erreur lors du traitement de cette liste : {e}")
            continue

    print("\nÉcriture du fichier final...")
    try:
        sorted_domains = sorted(list(final_domains))

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"# Fichier de blocage généré automatiquement\n")
            f.write(
                f"# Total des domaines uniques et valides : {len(sorted_domains)}\n"
            )
            f.write("#\n")
            for domain in sorted_domains:
                f.write(f"{domain}\n")

        print(
            f"🎉 Terminé ! Le fichier '{OUTPUT_FILE}' a été créé avec {len(sorted_domains)} domaines uniques et valides."
        )

    except IOError as e:
        print(f"Erreur: Impossible d'écrire dans le fichier '{OUTPUT_FILE}': {e}")


if __name__ == "__main__":
    generate_blocklist()
