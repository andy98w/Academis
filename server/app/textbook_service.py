
import logging
from typing import Dict, List, Union, Optional
#Note that this is hardcoded for now
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MICRO_TOC = {
    "type": "micro",
    "units": {
        1: {
            "title": "Basic Economic Concepts",
            "chapters": [
                {"chapter_number": "1.1", "title": "Scarcity and Choice"},
                {"chapter_number": "1.2", "title": "Opportunity Cost and the Production Possibilities Curve"},
                {"chapter_number": "1.3", "title": "Comparative Advantage and Trade"},
                {"chapter_number": "1.4", "title": "Economic Systems"}
            ]
        },
        2: {
            "title": "Supply and Demand",
            "chapters": [
                {"chapter_number": "2.1", "title": "Demand Fundamentals"},
                {"chapter_number": "2.2", "title": "Supply Fundamentals"},
                {"chapter_number": "2.3", "title": "Market Equilibrium and Price Determination"},
                {"chapter_number": "2.4", "title": "Price and Quantity Controls"}
            ]
        },
        3: {
            "title": "Production, Cost, and the Perfect Competition Model",
            "chapters": [
                {"chapter_number": "3.1", "title": "Production and Cost in the Short Run"},
                {"chapter_number": "3.2", "title": "Production and Cost in the Long Run"},
                {"chapter_number": "3.3", "title": "Perfect Competition Market Structure"},
                {"chapter_number": "3.4", "title": "Profit Maximization in Perfectly Competitive Markets"}
            ]
        },
        4: {
            "title": "Imperfect Competition",
            "chapters": [
                {"chapter_number": "4.1", "title": "Monopoly Market Structure"},
                {"chapter_number": "4.2", "title": "Price Discrimination"},
                {"chapter_number": "4.3", "title": "Monopolistic Competition"},
                {"chapter_number": "4.4", "title": "Oligopoly and Game Theory"}
            ]
        },
        5: {
            "title": "Factor Markets",
            "chapters": [
                {"chapter_number": "5.1", "title": "Derived Factor Demand"},
                {"chapter_number": "5.2", "title": "Marginal Revenue Product"},
                {"chapter_number": "5.3", "title": "Labor Market and Wages"},
                {"chapter_number": "5.4", "title": "Interest Rates and Capital Markets"}
            ]
        },
        6: {
            "title": "Market Failure and the Role of Government",
            "chapters": [
                {"chapter_number": "6.1", "title": "Externalities and Public Goods"},
                {"chapter_number": "6.2", "title": "Public Policy to Address Externalities"},
                {"chapter_number": "6.3", "title": "Income Distribution and Equity"},
                {"chapter_number": "6.4", "title": "Government Intervention in Markets"}
            ]
        },
        7: {
            "title": "Consumer Choice and Elasticity",
            "chapters": [
                {"chapter_number": "7.1", "title": "Utility Maximization"},
                {"chapter_number": "7.2", "title": "Consumer Surplus"},
                {"chapter_number": "7.3", "title": "Price, Income, and Cross Elasticities of Demand"},
                {"chapter_number": "7.4", "title": "Elasticity of Supply"}
            ]
        },
        8: {
            "title": "Firm Behavior and Market Structure",
            "chapters": [
                {"chapter_number": "8.1", "title": "Profit and Revenue Maximization"},
                {"chapter_number": "8.2", "title": "Firm Decision-Making"},
                {"chapter_number": "8.3", "title": "Market Power and Price Setting"},
                {"chapter_number": "8.4", "title": "Market Concentration and Regulation"}
            ]
        },
        9: {
            "title": "Market Efficiency and Equity",
            "chapters": [
                {"chapter_number": "9.1", "title": "Economic Efficiency and Deadweight Loss"},
                {"chapter_number": "9.2", "title": "Market Failures and Government Policies"},
                {"chapter_number": "9.3", "title": "Income Inequality and Redistribution"},
                {"chapter_number": "9.4", "title": "Taxation and Market Outcomes"}
            ]
        }
    }
}

MACRO_TOC = {
    "type": "macro",
    "units": {
        1: {
            "title": "Basic Economic Concepts",
            "chapters": [
                {"chapter_number": "1.1", "title": "Scarcity and Choice in Macroeconomics"},
                {"chapter_number": "1.2", "title": "Production Possibilities and Opportunity Cost"},
                {"chapter_number": "1.3", "title": "Comparative Advantage and Trade"},
                {"chapter_number": "1.4", "title": "Economic Systems and Macroeconomic Objectives"}
            ]
        },
        2: {
            "title": "Economic Indicators and the Business Cycle",
            "chapters": [
                {"chapter_number": "2.1", "title": "Measuring GDP and National Income"},
                {"chapter_number": "2.2", "title": "Unemployment and Inflation"},
                {"chapter_number": "2.3", "title": "Business Cycles"},
                {"chapter_number": "2.4", "title": "Economic Growth and Economic Development"}
            ]
        },
        3: {
            "title": "National Income and Price Determination",
            "chapters": [
                {"chapter_number": "3.1", "title": "Aggregate Demand"},
                {"chapter_number": "3.2", "title": "Aggregate Supply"},
                {"chapter_number": "3.3", "title": "Macroeconomic Equilibrium"},
                {"chapter_number": "3.4", "title": "Fiscal Policy and Economic Stability"}
            ]
        },
        4: {
            "title": "Financial Sector",
            "chapters": [
                {"chapter_number": "4.1", "title": "Money, Banking, and Financial Markets"},
                {"chapter_number": "4.2", "title": "Monetary Policy"},
                {"chapter_number": "4.3", "title": "The Money Market"},
                {"chapter_number": "4.4", "title": "The Loanable Funds Market"}
            ]
        },
        5: {
            "title": "Long-Run Consequences of Stabilization Policies",
            "chapters": [
                {"chapter_number": "5.1", "title": "Fiscal and Monetary Policy Actions"},
                {"chapter_number": "5.2", "title": "Government Deficits and the National Debt"},
                {"chapter_number": "5.3", "title": "Crowding Out and Economic Growth"},
                {"chapter_number": "5.4", "title": "Policy Debates and Economic Schools of Thought"}
            ]
        },
        6: {
            "title": "Open Economy—International Trade and Finance",
            "chapters": [
                {"chapter_number": "6.1", "title": "Balance of Payments Accounts"},
                {"chapter_number": "6.2", "title": "Exchange Rates and International Capital Flows"},
                {"chapter_number": "6.3", "title": "Effects of Changes in Trade and Capital Flows"},
                {"chapter_number": "6.4", "title": "Trade Restrictions and Trade Agreements"}
            ]
        }
    }
}

MICRO_CONTENT = {
    # Unit 1 content
    "1.1": [
        "Scarcity is the fundamental economic problem that arises because people have unlimited wants but resources are limited. In economics, scarcity refers to the basic fact that there are never enough resources to satisfy all human wants and needs.",
        "When faced with scarcity, individuals, businesses, and societies must make choices about how to allocate their limited resources. These choices involve tradeoffs, meaning that choosing one option requires giving up another alternative.",
        "Every choice made has an opportunity cost, which is the value of the next best alternative that must be given up when making a specific choice. For example, if a student chooses to study for an economics exam instead of playing video games, the opportunity cost is the enjoyment foregone from not playing the video games.",
        "In microeconomics, we examine how these individual choices about resource allocation affect prices, production, and distribution of goods and services across markets and firms."
    ],
    "1.2": [
        "The Production Possibilities Curve (PPC) or Production Possibilities Frontier (PPF) is a graphical representation of the alternative combinations of two goods that an economy can produce with its available resources and technology.",
        "The PPC illustrates several economic concepts: scarcity (points outside the curve are unattainable with current resources), efficiency (points on the curve represent efficient use of resources), inefficiency (points inside the curve indicate resources are not being fully utilized), and opportunity cost (the slope of the curve represents the tradeoff between the two goods).",
        "A typical PPC is bowed outward (concave to the origin) because resources are not perfectly adaptable to producing different goods. As more of one good is produced, increasingly more of the other good must be sacrificed, demonstrating increasing opportunity costs.",
        "Economic growth can be represented by an outward shift of the PPC, indicating that more of both goods can be produced with the same resources due to improvements in technology, increases in resource availability, or enhanced human capital."
    ],
    "1.3": [
        "Comparative advantage is the ability of an individual, business, or country to produce a good or service at a lower opportunity cost than others. It is a fundamental principle that explains why trade is beneficial.",
        "Absolute advantage, by contrast, refers to the ability to produce more of a good with the same resources. Having an absolute advantage doesn't necessarily mean trade will be beneficial; it's comparative advantage that determines the gains from specialization and trade.",
        "According to the principle of comparative advantage, total economic output is maximized when individuals or countries specialize in producing goods for which they have the lowest opportunity cost and then trade with others.",
        "The theory of comparative advantage explains why countries trade with each other even when one country might be more efficient at producing everything. By specializing and trading, both countries can consume more than they could produce in isolation."
    ],
    "1.4": [
        "Economic systems are the methods societies use to allocate scarce resources among competing uses. The three main types are traditional, command, and market economies, though most modern economies are mixed systems incorporating elements of both command and market structures.",
        "In a traditional economy, resource allocation decisions are based on custom, tradition, and inheritance. These systems typically exist in rural, agricultural societies and rely heavily on social relationships and established practices.",
        "Command economies feature government ownership of resources and centralized decision-making about production and distribution. In these systems, government planning agencies determine what goods to produce, how to produce them, and who receives them.",
        "Market economies rely on the interaction of supply and demand through price signals to allocate resources. Individuals and businesses make independent decisions about production, consumption, and resource allocation based on their own self-interest."
    ],
    
    # Unit 2 content
    "2.1": [
        "The demand curve represents the relationship between the price of a good and the quantity that consumers are willing and able to purchase at that price, holding all other factors constant (ceteris paribus).",
        "According to the law of demand, there is an inverse relationship between price and quantity demanded. As price increases, quantity demanded decreases; as price decreases, quantity demanded increases.",
        "A change in price causes a movement along the demand curve, which is called a change in quantity demanded. This is different from a shift of the entire demand curve, which is called a change in demand.",
        "Factors that can shift the demand curve (change demand) include changes in consumer income, prices of related goods (substitutes and complements), consumer preferences, expectations about future prices, and the number of buyers in the market."
    ],
    "2.2": [
        "The supply curve shows the relationship between the price of a good and the quantity that producers are willing and able to offer for sale at that price, holding all other factors constant.",
        "According to the law of supply, there is a direct relationship between price and quantity supplied. As price increases, quantity supplied increases; as price decreases, quantity supplied decreases.",
        "A change in price causes a movement along the supply curve, which is called a change in quantity supplied. This is different from a shift of the entire supply curve, which is called a change in supply.",
        "Factors that can shift the supply curve (change supply) include changes in input prices, technology, expectations, the number of sellers in the market, and government regulations or taxes."
    ],
    "2.3": [
        "Market equilibrium occurs at the price and quantity where the quantity demanded equals the quantity supplied. Graphically, this is the intersection point of the supply and demand curves.",
        "At the equilibrium price, the amount that buyers want to buy exactly equals the amount that sellers want to sell. There is no tendency for price to change unless there is a shift in either supply or demand.",
        "If the market price is above equilibrium (surplus), the quantity supplied exceeds the quantity demanded. This creates downward pressure on price as sellers compete to sell their products.",
        "If the market price is below equilibrium (shortage), the quantity demanded exceeds the quantity supplied. This creates upward pressure on price as buyers compete to purchase the limited supply of goods."
    ],
    "2.4": [
        "Price controls are government-imposed limits on the prices of goods and services in the market. The two main types are price ceilings and price floors.",
        "A price ceiling is a maximum price that can legally be charged for a good or service. When set below the equilibrium price, it creates a shortage because quantity demanded exceeds quantity supplied at the ceiling price. Examples include rent control and gasoline price ceilings during energy crises.",
        "A price floor is a minimum price that can legally be charged. When set above the equilibrium price, it creates a surplus because quantity supplied exceeds quantity demanded at the floor price. Examples include minimum wage laws and agricultural price supports.",
        "Quantity controls restrict the amount of a good that can be bought or sold. Examples include import quotas, production quotas, and licensing requirements. These controls create inefficiencies and often lead to black markets."
    ]
    # Additional units would be defined similarly...
}

MACRO_CONTENT = {
    # Unit 1 content
    "1.1": [
        "Scarcity in macroeconomics applies to the economy as a whole and focuses on how national economies allocate limited resources to meet the unlimited wants and needs of their populations.",
        "The concept of choice in macroeconomics is concerned with broader economic decisions such as how much of a nation's resources should be allocated to consumption versus investment, public versus private spending, or domestic versus international markets.",
        "Macroeconomics examines the aggregate consequences of individual choices, looking at how millions of decisions by households, firms, and governments interact to determine the overall health and direction of an economy.",
        "Unlike microeconomics, which focuses on individual markets, macroeconomics addresses economy-wide phenomena such as inflation, unemployment, economic growth, and the business cycle."
    ],
    "1.2": [
        "The Production Possibilities Curve (PPC) in macroeconomics often represents the tradeoff between different sectors of the economy, such as consumer goods versus capital goods, or civilian goods versus military goods.",
        "The opportunity cost concept at the macroeconomic level involves national priorities. For example, a country that devotes more resources to military spending has fewer resources available for healthcare, education, or infrastructure development.",
        "In macroeconomics, the PPC demonstrates the tradeoff between present consumption and investment for future growth. Points inside the curve indicate unemployment or inefficiency in the overall economy.",
        "Economic growth is shown as an outward shift of the entire PPC and can result from improvements in technology, increases in capital stock, better education and training of the workforce, or discovery of new resources."
    ],
    "1.3": [
        "Comparative advantage explains patterns of international trade and specialization among countries. According to this principle, countries benefit from specializing in producing goods for which they have the lowest opportunity cost and trading for other goods.",
        "Even when one country has an absolute advantage in producing all goods, both countries can still benefit from trade based on their comparative advantages. This is one of the most important and counterintuitive principles in economics.",
        "International trade based on comparative advantage leads to more efficient resource allocation globally, increased productivity, lower prices for consumers, and higher standards of living in trading nations.",
        "Trade barriers such as tariffs, quotas, and subsidies reduce the gains from comparative advantage and create economic inefficiencies, though they may benefit specific groups within an economy in the short term."
    ],
    "1.4": [
        "Economic systems at the macroeconomic level determine how national resources are allocated, how production decisions are made, and how goods and services are distributed throughout the economy.",
        "The main macroeconomic objectives that most economic systems try to achieve are full employment, price stability, economic growth, and equitable distribution of income.",
        "In market-oriented systems, these objectives are pursued primarily through indirect government policies that work with market forces, such as monetary and fiscal policy, rather than direct control of production.",
        "In more centrally planned systems, governments may directly control key industries, set prices, allocate resources, and determine production targets to achieve their macroeconomic objectives."
    ],
    
    # Unit 2 content
    "2.1": [
        "Gross Domestic Product (GDP) is the total market value of all final goods and services produced within a country's borders in a specific time period. It is the most comprehensive measure of economic activity in a nation.",
        "GDP can be calculated using three approaches: the expenditure approach (sum of all spending on final goods and services), the income approach (sum of all income earned in the production process), and the production approach (sum of value added at each stage of production).",
        "The expenditure approach calculates GDP as the sum of consumption (C), investment (I), government spending (G), and net exports (X - M): GDP = C + I + G + (X - M).",
        "National income measures include GDP, Gross National Product (GNP), Net National Product (NNP), National Income (NI), Personal Income (PI), and Disposable Personal Income (DPI), each giving different perspectives on a nation's economic performance."
    ],
    "2.2": [
        "Unemployment occurs when people are actively looking for work but cannot find jobs. The unemployment rate is calculated as the percentage of the labor force that is unemployed.",
        "Types of unemployment include frictional (temporary unemployment during job transitions), structural (mismatch between worker skills and job requirements), cyclical (related to business cycle downturns), and seasonal unemployment.",
        "Inflation is a sustained increase in the general price level of goods and services in an economy. It is typically measured using price indexes such as the Consumer Price Index (CPI) or the GDP deflator.",
        "The consequences of inflation include decreased purchasing power, uncertainty in business planning, redistribution of income and wealth, and distortions in economic decision-making. Different groups are affected differently by inflation."
    ],
    "2.3": [
        "The business cycle refers to the alternating periods of expansion and contraction in economic activity that economies experience over time. The four main phases are expansion, peak, contraction, and trough.",
        "During an expansion, GDP grows, unemployment falls, and economic activity increases. This phase ends at the peak, where economic activity reaches its maximum level in that cycle.",
        "A contraction (or recession) is characterized by declining GDP, rising unemployment, and reduced economic activity. A severe and prolonged contraction is called a depression. This phase ends at the trough, where economic activity reaches its minimum level.",
        "Business cycles vary in length and severity, and can be caused by various factors including changes in aggregate demand, supply shocks, monetary policy, and external events."
    ],
    "2.4": [
        "Economic growth refers to the increase in the production of goods and services over time, typically measured as the annual percentage change in real GDP. Long-term economic growth increases a nation's standard of living.",
        "Sources of economic growth include increases in the quantity and quality of resources (labor, capital, land), technological innovation, improved education and training, better institutional frameworks, and more efficient resource allocation.",
        "Economic development is a broader concept than economic growth, encompassing improvements in human well-being including health, education, environmental quality, and social equality, not just increases in GDP.",
        "Measures of economic development include the Human Development Index (HDI), which combines indicators of life expectancy, education, and per capita income, as well as measures of poverty, inequality, and access to basic services."
    ]
}

async def get_textbook_toc(economics_type: str) -> dict:
    """
    Get the static table of contents for the economics textbook.
    
    Args:
        economics_type: Either "micro" or "macro"
        
    Returns:
        Dictionary with textbook table of contents
    """
    logger.info(f"Getting {economics_type} textbook table of contents")
    
    try:
        if economics_type.lower() == "micro":
            return MICRO_TOC
        else:
            return MACRO_TOC
    
    except Exception as e:
        logger.error(f"Error getting textbook TOC: {str(e)}")
        return {"error": str(e)}

async def get_textbook_content(economics_type: str, unit: int = None, chapter: str = None) -> dict:
    """
    Retrieve static textbook content organized by units and chapters.
    
    Args:
        economics_type: Either "micro" or "macro"
        unit: Optional unit number (1-9 for micro, 1-6 for macro)
        chapter: Optional chapter name/title
        
    Returns:
        Dictionary with textbook content organized by units and chapters
    """
    logger.info(f"Retrieving {economics_type} textbook content for unit: {unit}, chapter: {chapter}")
    
    try:
        toc = await get_textbook_toc(economics_type)
        
        content_by_chapter = MICRO_CONTENT if economics_type.lower() == "micro" else MACRO_CONTENT

        result = {
            "type": economics_type,
            "units": {}
        }
        
        if unit is not None:
            if unit not in toc["units"]:
                raise ValueError(f"Unit {unit} not found in {economics_type}economics textbook")
                
            unit_data = toc["units"][unit]
            result["units"][unit] = {
                "title": unit_data["title"],
                "chapters": {}
            }
            
            if chapter:
                chapter_found = False
                for ch_data in unit_data["chapters"]:
                    if chapter.lower() in ch_data["title"].lower() or chapter == ch_data["chapter_number"]:
                        chapter_found = True
                        chapter_key = ch_data["chapter_number"]
                        chapter_title = ch_data["title"]
                        
                        if chapter_key in content_by_chapter:
                            result["units"][unit]["chapters"][chapter_title] = content_by_chapter[chapter_key]
                        else:
                            result["units"][unit]["chapters"][chapter_title] = [
                                f"This chapter covers {chapter_title} within {unit_data['title']}.",
                                f"It explores key concepts and applications related to {chapter_title}.",
                                f"Students will learn about the theoretical frameworks and practical implications of {chapter_title} in {economics_type}economics."
                            ]
                
                if not chapter_found:
                    raise ValueError(f"Chapter '{chapter}' not found in Unit {unit}")
            else:
                for ch_data in unit_data["chapters"]:
                    chapter_key = ch_data["chapter_number"]
                    chapter_title = ch_data["title"]
                    
                    if chapter_key in content_by_chapter:
                        result["units"][unit]["chapters"][chapter_title] = content_by_chapter[chapter_key]
                    else:
                        result["units"][unit]["chapters"][chapter_title] = [
                            f"This chapter covers {chapter_title} within {unit_data['title']}.",
                            f"It explores key concepts and applications related to {chapter_title}.",
                            f"Students will learn about the theoretical frameworks and practical implications of {chapter_title} in {economics_type}economics."
                        ]
        else:
            for unit_num, unit_data in toc["units"].items():
                result["units"][unit_num] = {
                    "title": unit_data["title"],
                    "summary": f"Unit {unit_num}: {unit_data['title']} covers key concepts in {economics_type}economics including " + 
                              ", ".join([ch["title"] for ch in unit_data["chapters"][:2]]) + 
                              f", and other topics. This unit contains {len(unit_data['chapters'])} chapters."
                }
                
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving textbook content: {str(e)}")
        return {"error": str(e)}

async def generate_textbook_content(economics_type: str, unit: int, chapter: str) -> List[str]:
    """
    Generate textbook content for a specific chapter using an AI model.
    This would be used to expand the static content with more dynamic content.
    
    Args:
        economics_type: Either "micro" or "macro"
        unit: Unit number
        chapter: Chapter identifier
        
    Returns:
        List of paragraphs with content for the chapter
    """
    # This is a placeholder
    logger.info(f"Generating content for {economics_type} Unit {unit}, Chapter {chapter}")
    
    return [
        f"This is dynamically generated content for {economics_type}economics Unit {unit}, Chapter {chapter}."
    ]