"""
concepts.py -- DOMAIN CONFIG for the BBNJ / High Seas Treaty corpus.

Neutral concept vocabulary for the derived layer. Concepts describe what a provision is
*about*; they take NO side in the "freedom of the high seas" vs "common heritage of mankind"
debate, and make no claim about adequacy or ambition. Everything here lands in derived/,
labelled unofficial and traceable to an authoritative text hash.

Backbone: the Agreement's four substantive elements (MGRs+benefit-sharing, ABMTs/MPAs, EIAs,
CB&TT) plus the cross-cutting institutional, financial, compliance, dispute-settlement,
relationship and final-clause matters.
"""

# ---- neutral concept vocabulary ---------------------------------------------
VOCAB = {
    "scope_and_definitions": "Use of terms, objective, scope of application and exceptions.",
    "general_principles_and_approaches": "The principles and approaches stated to guide the Agreement (e.g. precaution, ecosystem approach, equity, best available science), described without endorsement.",
    "marine_genetic_resources": "Access to and utilization of marine genetic resources and digital sequence information of areas beyond national jurisdiction.",
    "benefit_sharing": "Fair and equitable sharing of monetary and non-monetary benefits from marine genetic resources.",
    "area_based_management_tools": "Area-based management tools, including marine protected areas: proposals, establishment, criteria and decision-making.",
    "environmental_impact_assessment": "Screening, assessment, monitoring and review of the environmental impacts of activities, including cumulative and strategic assessment.",
    "capacity_building_and_technology_transfer": "Capacity-building and the transfer of marine technology, in particular to developing States Parties.",
    "institutional_arrangements": "Bodies of the Agreement: Conference of the Parties, Scientific and Technical Body, secretariat and subsidiary bodies.",
    "clearing_house_mechanism": "The clearing-house mechanism and information-sharing infrastructure of the Agreement.",
    "financial_resources_and_mechanism": "Financial resources, the financial mechanism, funds, contributions and budget.",
    "implementation_and_compliance": "National implementation measures, monitoring of implementation, and the Implementation and Compliance Committee.",
    "dispute_settlement": "Prevention and settlement of disputes, including the relationship to Part XV of the Convention.",
    "relationship_with_other_instruments": "Relationship with UNCLOS and with relevant legal instruments, frameworks and global, regional, subregional and sectoral bodies (the 'not undermine' clause).",
    "rights_interests_and_knowledge": "The balance of rights and interests, special interests of developing States, and the rights and traditional knowledge of Indigenous Peoples and local communities.",
    "final_provisions": "Signature, ratification, accession, entry into force, amendment, reservations, voting, denunciation, depositary and authentic texts.",
}

# ---- curated tags (corpus_id -> [ [unit, [concepts]] ]) ----------------------
# Left empty for now: the keyword fallback tags the first ingested instrument. Upgrade the
# flagship Agreement to curated, provision-level tags after a human review pass.
TAGS = {
    "un/bbnj-agreement-2023": [
        ["preamble/chapeau", ["scope_and_definitions", "general_principles_and_approaches", "rights_interests_and_knowledge"]],
        ["Article 1", ["scope_and_definitions"]],
        ["Article 2", ["scope_and_definitions"]],
        ["Article 3", ["scope_and_definitions"]],
        ["Article 4", ["scope_and_definitions"]],
        ["Article 5", ["relationship_with_other_instruments", "scope_and_definitions"]],
        ["Article 6", ["scope_and_definitions", "rights_interests_and_knowledge"]],
        ["Article 7", ["general_principles_and_approaches"]],
        ["Article 8", ["general_principles_and_approaches", "relationship_with_other_instruments"]],
        ["Article 9", ["marine_genetic_resources", "benefit_sharing"]],
        ["Article 10", ["marine_genetic_resources", "scope_and_definitions"]],
        ["Article 11", ["marine_genetic_resources"]],
        ["Article 12", ["marine_genetic_resources", "clearing_house_mechanism"]],
        ["Article 13", ["marine_genetic_resources", "rights_interests_and_knowledge"]],
        ["Article 14", ["benefit_sharing"]],
        ["Article 15", ["benefit_sharing", "institutional_arrangements"]],
        ["Article 16", ["benefit_sharing", "marine_genetic_resources"]],
        ["Article 17", ["area_based_management_tools"]],
        ["Article 18", ["area_based_management_tools", "rights_interests_and_knowledge"]],
        ["Article 19", ["area_based_management_tools"]],
        ["Article 20", ["area_based_management_tools", "institutional_arrangements"]],
        ["Article 21", ["area_based_management_tools"]],
        ["Article 22", ["area_based_management_tools"]],
        ["Article 23", ["area_based_management_tools", "institutional_arrangements"]],
        ["Article 24", ["area_based_management_tools"]],
        ["Article 25", ["area_based_management_tools", "implementation_and_compliance"]],
        ["Article 26", ["area_based_management_tools", "implementation_and_compliance"]],
        ["Article 27", ["environmental_impact_assessment"]],
        ["Article 28", ["environmental_impact_assessment"]],
        ["Article 29", ["environmental_impact_assessment", "relationship_with_other_instruments"]],
        ["Article 30", ["environmental_impact_assessment"]],
        ["Article 31", ["environmental_impact_assessment"]],
        ["Article 32", ["environmental_impact_assessment", "clearing_house_mechanism"]],
        ["Article 33", ["environmental_impact_assessment"]],
        ["Article 34", ["environmental_impact_assessment", "institutional_arrangements"]],
        ["Article 35", ["environmental_impact_assessment", "implementation_and_compliance"]],
        ["Article 36", ["environmental_impact_assessment"]],
        ["Article 37", ["environmental_impact_assessment"]],
        ["Article 38", ["environmental_impact_assessment", "institutional_arrangements"]],
        ["Article 39", ["environmental_impact_assessment"]],
        ["Article 40", ["capacity_building_and_technology_transfer"]],
        ["Article 41", ["capacity_building_and_technology_transfer"]],
        ["Article 42", ["capacity_building_and_technology_transfer"]],
        ["Article 43", ["capacity_building_and_technology_transfer"]],
        ["Article 44", ["capacity_building_and_technology_transfer"]],
        ["Article 45", ["capacity_building_and_technology_transfer", "implementation_and_compliance"]],
        ["Article 46", ["capacity_building_and_technology_transfer", "institutional_arrangements"]],
        ["Article 47", ["institutional_arrangements"]],
        ["Article 48", ["institutional_arrangements"]],
        ["Article 49", ["institutional_arrangements"]],
        ["Article 50", ["institutional_arrangements"]],
        ["Article 51", ["clearing_house_mechanism", "institutional_arrangements"]],
        ["Article 52", ["financial_resources_and_mechanism"]],
        ["Article 53", ["implementation_and_compliance"]],
        ["Article 54", ["implementation_and_compliance"]],
        ["Article 55", ["implementation_and_compliance", "institutional_arrangements"]],
        ["Article 56", ["dispute_settlement"]],
        ["Article 57", ["dispute_settlement"]],
        ["Article 58", ["dispute_settlement"]],
        ["Article 59", ["dispute_settlement"]],
        ["Article 60", ["dispute_settlement", "relationship_with_other_instruments"]],
        ["Article 61", ["dispute_settlement"]],
        ["Article 62", ["relationship_with_other_instruments"]],
        ["Article 63", ["general_principles_and_approaches", "rights_interests_and_knowledge"]],
        ["Article 64", ["final_provisions", "institutional_arrangements"]],
        ["Article 65", ["final_provisions"]],
        ["Article 66", ["final_provisions"]],
        ["Article 67", ["final_provisions"]],
        ["Article 68", ["final_provisions"]],
        ["Article 69", ["final_provisions"]],
        ["Article 70", ["final_provisions"]],
        ["Article 71", ["final_provisions"]],
        ["Article 72", ["final_provisions"]],
        ["Article 73", ["final_provisions"]],
        ["Article 74", ["final_provisions"]],
        ["Article 75", ["final_provisions"]],
        ["Article 76", ["final_provisions"]],
        ["ANNEX I", ["area_based_management_tools"]],
        ["ANNEX II", ["capacity_building_and_technology_transfer"]],
    ],
}

# ---- keyword fallback (concept -> substrings, lower-case) --------------------
KW = {
    "scope_and_definitions": ["use of terms", "for the purposes of this agreement", "scope of application", "general objective", "exceptions", "” means"],
    "general_principles_and_approaches": ["principle", "approach", "precaution", "polluter", "ecosystem", "best available science", "common heritage", "freedom of the high seas", "equitab"],
    "marine_genetic_resources": ["marine genetic resource", "genetic resources", "digital sequence information", "collection in situ", "utilization of marine genetic", "access to marine genetic"],
    "benefit_sharing": ["benefit-sharing", "sharing of benefits", "fair and equitable", "monetary benefit", "non-monetary", "special fund"],
    "area_based_management_tools": ["area-based management", "marine protected area", "network of marine protected", "designated area", "conservation and sustainable use objectives"],
    "environmental_impact_assessment": ["environmental impact assessment", "impact assessment", "screening", "cumulative impact", "strategic environmental assessment", "monitoring, reporting and review"],
    "capacity_building_and_technology_transfer": ["capacity-building", "transfer of marine technology", "developing states parties", "technical assistance", "development and transfer"],
    "institutional_arrangements": ["conference of the parties", "scientific and technical body", "secretariat", "subsidiary body", "rules of procedure"],
    "clearing_house_mechanism": ["clearing-house mechanism", "clearing-house", "information-sharing", "open-access", "platform"],
    "financial_resources_and_mechanism": ["financial mechanism", "financial resources", "voluntary trust fund", "contribution", "budget", "special fund", "finance committee"],
    "implementation_and_compliance": ["necessary legislative", "monitor the implementation", "implementation and compliance committee", "compliance", "report to the conference"],
    "dispute_settlement": ["dispute", "settlement of disputes", "arbitration", "tribunal", "part xv", "peaceful means", "conciliation", "international court of justice"],
    "relationship_with_other_instruments": ["not undermine", "relevant legal instruments and frameworks", "regional, subregional", "sectoral bodies", "relationship between this agreement and the convention"],
    "rights_interests_and_knowledge": ["indigenous peoples", "local communities", "traditional knowledge", "landlocked", "sovereignty", "sovereign rights", "special interests and needs"],
    "final_provisions": ["signature", "ratification", "accession", "entry into force", "amendment", "reservation", "denunciation", "depositary", "authentic", "right to vote", "secretary-general of the united nations"],
}

# ---- structure extraction: how provisions are headed in this domain ----------
UNIT_HEADERS = ["Article", "Annex", "ANNEX", "Section", "Principle", "Artículo", "ANNEXE", "ANEXO", "Статья", "ПРИЛОЖЕНИЕ"]

# ---- cross-references to detect (regexes) ------------------------------------
CITATION_PATTERNS = [
    r"[Aa]rticle\s+\d+[A-Za-z]*",
    r"[Pp]art\s+[IVXLCDM]+",
    r"[Aa]nnex\s+[IVX]+",
    r"the Convention",
]
