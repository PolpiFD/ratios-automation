import os
import getpass
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

#A delete quand ça passe par le main
from dotenv import load_dotenv
load_dotenv()

#teser la clé OpenAI
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter une clé API pour OpenAI")


system_prompt = ChatPromptTemplate.from_template(
    """
<Role>
Ton rôle est de classer des documents en plusieurs catégories.

<contexte>
Tu agis pour le compte d'une fiduciaire en Suisse Romande.

Uniquement les catégories mentionnées dans 'Classification' devront être utilisées.

Attention de ne pas confondre les Débiteurs et Créanciers !
Le nom du client te sera transmis, les facture qui seront transmise sous ce même nom, seront donc logiquement des débiteurs.

Information sur le document :
{input}
"""
)

class Classification(BaseModel):
    categorie: str = Field(
        ...,
        description="Cela correspond à la catégorie qui à laquelle appartient le document comptable",
        enum=["Créancier", "Débiteur", "Banque", "Ticket"]
    ),
    score: int = Field(
        ...,
        description="Score de confiance sur la classification allant de 1% à 100% (1 signfie que c'est certain que le document est mal classifié, 100 nous sommes absolu sur du résultat)"
    )

llm = ChatOpenAI(temperature=0.2, model="gpt-4.1-nano").with_structured_output(
    Classification
)

inp = """


"""


async def data_classification(result: str):
    return None