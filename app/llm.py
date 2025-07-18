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
    )
    score: int = Field(
        ...,
        description="Score de confiance sur la classification allant de 1% à 100% (1 signfie que c'est certain que le document est mal classifié, 100 nous sommes absolu sur du résultat)"
    )

llm = ChatOpenAI(temperature=0.2, model="gpt-4.1-nano").with_structured_output(
    Classification
)


inp = """
ESPERANZA\n03 JUIN 2025\n875905\nVU POUR PAIEMENT\nSignature :\nDate :\n1\nPoste PFI20070103\nFr. :\n421 .-\nPos. budg. :\n3170100-01\nO. P. no 7605\nVisa : ea\nJardin Botanique de l'Université de Fribourg Chemin du Musée 10 1700 Fribourg\nTél. 026 300 88 86\nFACTURE 620194\nDate du document\n19.05.2025\nDocument\n20368\nClient\n29305\nNotre référence\nLes Cafés Esperanza Sarl\nVotre référence\nJardin Botanique de l'Université de Fribourg\nDésignation\nProduit\nQuantité Unité\nPrix unitaire\nTVA\nMontant TTC\nLocation courte durée, Machine X7 - 777164 Nombre de consommations\n777164\n177\n1.00000\n2.6\n177.00\nLocation courte durée, Machine X7 - 777120 Nombre de consommations\n777120\n204\n1.00000\n2.6\n204.00\nForfait de prise en charge, y.c. assurance- dommage (Prix par machine)\n10\n2\n20.00000\n8.1\n40.00\nKit café et consommables Location Courte Durée pour 200 consommations\nKT176\n1\nKit café et consommables Location Courte Durée pour 200 consommations\nKT152\n1\nOKMH\nKit café et consommables Location Courte Durée pour 200 consommations\nKT283\n1\nLes Cafés Esperanza Sàrl, rue des Artisans 136, CH-1628 Vuadens Torréfaction artisanale · Solutions café · Machines automatiques & Services Alles rund um den Kaffee · Kaffeemaschinen kaufen & finanzieren · Service Abo FLO-ID 2120 · CHE-105.245.963 TVA\nTél. 026 919 80 80 · Fax 026 919 80 81 · info@esperanza.ch Commande/Bestellung 026 919 80 80 · order@esperanza.ch Finance & Admin. 026 919 80 84 · admin@esperanza.ch\nFACTURE 620194 pour Jardin Botanique de l'Université de Fribourg, 1700 Fribourg\nPage 2/2\nDésignation Produit\nQuantité Unité\nPrix unitaire\nTVA\nMontant TTC\nChers partenaires, amis et spécialistes du café,\nChez Esperanza, nous tâchons de vous garantir un café savoureux. Au travail ou durant vos loisirs, notre objectif est de répondre à vos attentes. Nous vous remercions de votre confiance et sommes heureux de vous compter parmi nos clients.\nCordialement,\nLes Cafés Esperanza\nConditions de paiement\n30 jours NET\nEchéance\n18.06.2025\nQuantité totale\n386\nCoordonnées bancaires\nMontant HT\nTVA\nMontant TVA\n371.34\n2.60\n9.65\n37.00\n8.10\n3.00\nBanque cantonale de Fribourg 1701 Fribourg IBAN : CH50 0076 8300 1163 8150 9\nTotal brut HT\n408.35\nTotal net HT\n408.35\nTotal TVA\n12.65\nTOTAL TTC\n421.00\nMontant en CHF\nLes Cafés Esperanza Sàrl, rue des Artisans 136, CH-1628 Vuadens Torréfaction artisanale · Solutions café · Machines automatiques & Services Alles rund um den Kaffee · Kaffeemaschinen kaufen & finanzieren · Service Abo FLO-ID 2120 · CHE-105.245.963 TVA\nTél. 026 919 80 80 · Fax 026 919 80 81 · info@esperanza.ch Commande/Bestellung 026 919 80 80 · order@esperanza.ch Finance & Admin. 026 919 80 84 · admin@esperanza.ch\nFACTURE 620194 30 jours NET\nDate : 19.05.2025\nEchéance :\n18.06.2025\nwww.esperanza.ch Les Cafés Esperanza Sarl 026 919 80 80 | info@esperanza.ch\nf\nlescafesesperanza\nARTISANAT nous torréfions nos cafés au tambour, par petits lots, en Gruyère\nDONNER DU SENS\nHUMAIN nous tissons des liens, dans le respect et la bienveillance\nFAIRTRADE nos cafés sont issus du commerce équitable et labellisés Max Havelaar\nFRAÎCHEUR nos cafés sont conditionnés dans des sachets à valve, pour une conservation optimale\nFacture - si facile. Recevez et payez vos factures directement dans votre e-banking.\neBill\neBill. La facture numérique pour la Suisse. eBill.ch\nRécépissé\nCompte / Payable à CH72 3076 8300 1163 8150 9 Les Cafés Esperanza Sarl Rue des Artisans 136 1628 Vuadens\nRéférence 90 46880 00000 62019 40002 93057\nPayable par\nJardin Botanique de l'Université de\nFribourg\nChemin du Musée 10\n1700 Fribourg\nMonnaie\nMontant\nCHF\n421.00\nPoint de dépôt\nSection paiement\nMonnaie\nMontant\nCHF\n421.00\nCompte / Payable à CH72 3076 8300 1163 8150 9 Les Cafés Esperanza Sarl Rue des Artisans 136 1628 Vuadens\nRéférence 90 46880 00000 62019 40002 93057\nInformations supplémentaires //S1/10/620194/11/250519/20/20368/32/2.6:371.34;8.1 :37/40/0:30\nPayable par Jardin Botanique de l'Université de Fribourg Chemin du Musée 10 1700 Fribourg\nDécompte machine : 777164\nDécompte de départ\n29305 Jardin Botanique de l'Université de Fribourg Chemin du Musée 10 1700 Fribourg\nDate / Heure : 08/05/2025 08:23\nDépositaire : Les Cafés Esperanza Sarl\n1 petit café\n1 grand café\n1 café spécial\n1 capuccino\n2 petits cafés\n2 grands cafés\nEau\n7 088\n16 216\n177\n2 x 4 198\n2 x 13 626\n4 560\nTotal général 1\n63 689\nDécompte de retour\nDate / Heure : 13/05/2025 11:26\n1 petit café\n1 grand café\n1 café spécial\n1 capuccino\n2 petits cafés\n2 grands cafés\nEau\n7 116\n16 279\n177\n2 × 4 205\n2 x 13 661\n4 562\nTotal général 2\n63 866\nDécompte des consommations\nTotal général 1\n63 689\nTotal général 2\n63 866\nTotal des consommations\n177\nx Prix unitaire : 1,10\nFC620194\nMontant :\n194,70 :selected:\nDécompte machine : 777120\nDécompte de départ\n29305 Jardin Botanique de l'Université de Fribourg Chemin du Musée 10 1700 Fribourg\nDate / Heure : 08/05/2025 08:23\nDépositaire : Les Cafés Esperanza Sarl\n1 petit café\n1 grand café\n1 café spécial\n1 capuccino\n2 petits cafés\n2 grands cafés\nEau\n6 644\n12 013\n99\n2 x 4 338\n2 x 7 997\n4 449\nTotal général 1 47 875\nDécompte de retour\nDate / Heure : 13/05/2025 11:27\n1 petit café\n1 grand café\n1 café spécial\n1 capuccino\n2 petits cafés\n2 grands cafés\nEau\n6 656\n12 108\n99\n2 x 4 340\n2 x 8 043\n4 450\nTotal général 2 48 079\nDécompte des consommations\nTotal général 1\n47 875\nTotal général 2\n48 079\nTotal des consommations\n204\nx Prix unitaire : 1,10\nFC620194\nMontant :\n224,40	
"""
prompt = system_prompt.invoke({"input": inp})
response = llm.invoke(prompt)
print(response)

async def data_classification(result: str):
    return None