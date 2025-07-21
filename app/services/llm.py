import os
import getpass
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


#teser la clé OpenAI
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter une clé API pour OpenAI")

async def categorisation(content: str, name_client: str):
    system_prompt = ChatPromptTemplate.from_template(
    """
    ## <ROLE>
    Vous êtes un expert comptable spécialisé dans l'analyse et la catégorisation de documents financiers suisses. 
    Votre tâche est de classifier avec précision les documents comptables selon leur nature.
    </ROLE>

    ## <TASK>
    Analysez le contenu OCR du document fourni et déterminez sa catégorie parmi les 4 options suivantes :
    - Créanciers
    - Débiteurs  
    - Banque
    - Tickets

    Basez votre décision sur les critères de classification définis ci-dessous.
    </TASK>

    ## <CONTEXT>
    ### Document OCR à analyser :
    {document}
    ### Nom du client : {name_client}
    </CONTEXT>

    ## <CLASSIFICATION_RULES>

    ### Débiteurs
    - **Critère principal** : La facture est émise PAR le client
    - **Identification** : L'adresse/nom de l'émetteur (généralement en haut du document) correspond au nom du client fourni
    - **Indicateurs** : 
    - En-tête du document contient le nom/adresse du client
    - Document de type "Facture" ou "Invoice" émis par le client
    - Numéro de facture du client visible
    - Mention 'payable à .. NOM_DU_CLIENT' au niveau des informations de paiement.
    - Le nom du client peut légèrement varié sur la facture, par exemple : 
          - Ratios Conseils Sàrl === Ratios Innovative Finance 
    


    ### Créanciers  
    - **Critère principal** : La facture est émise par un fournisseur
    - **Identification** : L'adresse/nom de l'émetteur ne correspond PAS au client, mais le client apparaît comme destinataire
    - **Indicateurs** :
    - En-tête du document contient un nom d'entreprise différent du client
    - Le nom du client apparaît dans la section "Facturé à" ou "Destinataire"
    - Document reçu d'un fournisseur externe


    ### Banque
    - **Critère principal** : Document émis par une institution bancaire suisse
    - **Identification** : Le document commence par ou contient prominemment le nom d'une banque suisse
    - **Banques suisses courantes** :
    - Raiffeisen, BCV (Banque Cantonale Vaudoise), BCF, BCVS, BCGE, BCJU
    - Crédit Suisse, UBS, La Poste (PostFinance)
    - Migros Bank, Coop Bank, Alternative Bank Switzerland
    - **Types de documents** : Relevés bancaires, avis de débit/crédit, extraits de compte

    ### Tickets
    - **Critère principal** : Petits achats ou dépenses courantes
    - **Identification** : Documents de faible montant ou provenant d'établissements de service
    - **Indicateurs** :
    - Restaurants, cafés, bars
    - Stations-service, parkings
    - Magasins de détail, supermarchés
    - Transport public, taxis
    - Montants généralement inférieurs à 500 CHF
    - Format de reçu/ticket de caisse
    </CLASSIFICATION_RULES>

    ## <ANALYSIS_PROCESS>
    1. **Identifier l'émetteur** : Examinez l'en-tête du document pour déterminer qui a émis le document
    2. **Comparer avec le nom du client** : Vérifiez si l'émetteur correspond au client fourni
    3. **Rechercher les banques suisses** : Scannez le document pour les noms d'institutions bancaires
    4. **Évaluer le type de transaction** : Déterminez s'il s'agit d'une petite dépense courante
    5. **Appliquer la logique de classification** selon les règles définies
    </ANALYSIS_PROCESS>

    ## <OUTPUT_INSTRUCTIONS>
    - Analysez attentivement le contenu OCR
    - Appliquez les critères de classification dans l'ordre de priorité
    - En cas d'ambiguïté, privilégiez l'identification de l'émetteur du document
    - Fournissez uniquement la catégorie finale sans explication supplémentaire
    </OUTPUT_INSTRUCTIONS>

    ## <EXAMPLES>

    ### Exemple Débiteurs
    Document OCR contenant : "ENTREPRISE MARTIN SA, Rue du Commerce 12, 1000 Lausanne, FACTURE N° 2024-001"
    Client : "ENTREPRISE MARTIN SA"
    → Classification : Débiteurs (le client est l'émetteur)

    ### Exemple Créanciers  
    Document OCR contenant : "FOURNISSEUR TECH SARL, Avenue de la Paix 5, 1200 Genève, Facturé à : ENTREPRISE MARTIN SA"
    Client : "ENTREPRISE MARTIN SA" 
    → Classification : Créanciers (facture reçue d'un fournisseur)

    ### Exemple Banque
    Document OCR contenant : "BANQUE CANTONALE VAUDOISE, Relevé de compte, Période du 01.01.2024 au 31.01.2024"
    → Classification : Banque (document bancaire identifié)

    ### Exemple Tickets
    Document OCR contenant : "RESTAURANT LE PIGEON, Rue Centrale 8, Addition N°1234, Total : 45.50 CHF"
    → Classification : Tickets (petit achat restaurant)
    </EXAMPLES>
    """
    )

    class Classification(BaseModel):
        categorie: str = Field(
            ...,
            description="""
            Cela correspond à la catégorie qui à laquelle appartient le document comptable
            """,
            enum=["01 - Créanciers", "02 - Débiteurs", "03 - Banque", "04 - Tickets"]
        )
        score: int = Field(
            ...,
            description="Score de confiance sur la classification allant de 1% à 100% (1 signfie que c'est certain que le document est mal classifié, 100 nous sommes absolu sur du résultat)"
        )
        year: int = Field(
            ...,
            description="Année d'émission et/ou de paiement du document.",
        )

    llm = ChatOpenAI(temperature=0.2, model="gpt-4.1").with_structured_output(
        Classification
    )

    prompt = system_prompt.invoke({"document": content, "name_client": name_client})
    response = llm.invoke(prompt)
    return response

