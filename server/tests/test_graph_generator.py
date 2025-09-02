#!/usr/bin/env python3
"""
Test script for UniversalGraphGenerator's generate_contextual_graph function
"""

import sys
import os
import asyncio
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add server directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.dirname(current_dir)
sys.path.insert(0, server_dir)

from app.graph_service import UniversalGraphGenerator

async def test_ai_response():
    """Test just the AI response parsing to see what's being returned"""
    print("Testing AI response parsing...")
    print("=" * 60)
    
    generator = UniversalGraphGenerator()
    
    # Test the _analyze_visualization_need method directly
    content = "The supply and demand curves show the relationship between price and quantity."
    title = "Supply and Demand"
    
    print(f"Testing with content: {content}")
    print(f"Title: {title}")
    
    try:
        # Call the private method directly to see what it returns
        response = await generator._analyze_visualization_need(content, title)
        print(f"Raw response: {response}")
        
        if isinstance(response, dict):
            print(f"✅ Successfully parsed as dict: {response}")
        else:
            print(f"❌ Response is not a dict: {type(response)}")
            
    except Exception as e:
        print(f"❌ Error in _analyze_visualization_need: {e}")
        import traceback
        traceback.print_exc()
    
    # Let's also test the raw AI call to see what's being returned
    print("\n" + "-" * 40)
    print("Testing raw AI response...")
    
    from langchain.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    import json
    
    model = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_template("""
    Analyze this educational content to determine if it contains concepts that would benefit from visual representation.
    
    Title: {context_title}
    Content: {content}
    
    Look for:
    - Relationships between two or more variables/concepts
    - Comparisons or trade-offs
    - Processes or flows
    - Trends, patterns, or changes over time/conditions
    - Mathematical or logical relationships
    - Abstract concepts that could be made concrete through visualization
    
    Return JSON:
    {{
        "needs_visualization": true/false,
        "confidence": 0-100,
        "primary_concepts": ["concept1", "concept2"],
        "relationship_type": "positive/negative/inverse/cyclical/comparative/process/other",
        "reasoning": "explanation of why visualization would help"
    }}
    
    Be generous - if there are ANY relationships or concepts that could be clearer with a visual aid, suggest visualization.
    """)
    
    chain = prompt | model | StrOutputParser()
    
    try:
        raw_response = await chain.ainvoke({
            "content": content,
            "context_title": title
        })
        
        print(f"Raw AI response: {repr(raw_response)}")
        print(f"Response length: {len(raw_response)}")
        
        # Try to parse it
        try:
            parsed = json.loads(raw_response.strip())
            print(f"✅ Successfully parsed JSON: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Response content: {raw_response}")
            
    except Exception as e:
        print(f"❌ Error in raw AI call: {e}")
        import traceback
        traceback.print_exc()

async def test_graph_generation():
    """Test the UniversalGraphGenerator with simple input text"""
    
    # Initialize the graph generator
    generator = UniversalGraphGenerator()
    
    # Create Downloads directory path
    downloads_dir = os.path.expanduser("~/Downloads/graphs")
    os.makedirs(downloads_dir, exist_ok=True)
    print(f"Graphs will be saved to: {downloads_dir}")
    
    # Test cases with different types of content
    test_cases = [
        {
            "name": "Supply and Demand",
            "content": "The supply and demand curves show the relationship between price and quantity. When price increases, quantity supplied increases while quantity demanded decreases. The equilibrium point is where supply equals demand.",
            "title": "Supply and Demand Analysis"
        },
        {
            "name": "Production Possibility Frontier",
            "content": "A production possibility frontier (PPF) shows the maximum combinations of two goods that can be produced given available resources and technology. Points on the curve represent efficient production, while points inside represent inefficient production.",
            "title": "PPF Example"
        },
        {
            "name": "Market Equilibrium",
            "content": "Market equilibrium occurs when the quantity supplied equals the quantity demanded at a particular price. This creates a stable market price where there is no tendency for price to change.",
            "title": "Market Equilibrium"
        },
        {
            "name": "Simple Text (No Graph)",
            "content": "Economics is the study of how societies allocate scarce resources. It helps us understand how people make decisions and how markets work.",
            "title": "Economics Introduction"
        }
    ]
    
    print("Testing UniversalGraphGenerator.generate_contextual_graph()")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Content: {test_case['content'][:100]}...")
        print(f"Title: {test_case['title']}")
        
        try:
            # Call the generate_contextual_graph function
            result = await generator.generate_contextual_graph(
                test_case['content'], 
                test_case['title']
            )
            
            if result:
                print(f"✅ Graph generated successfully!")
                print(f"   Type: {result.get('type', 'unknown')}")
                print(f"   Title: {result.get('title', 'no title')}")
                print(f"   Description: {result.get('description', 'no description')[:100]}...")
                print(f"   Image data length: {len(result.get('image', ''))} characters")
                
                # Save the graph to Downloads directory
                image_data = result.get('image', '')
                if image_data:
                    # Create a safe filename
                    safe_title = "".join(c for c in test_case['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title.replace(' ', '_')
                    filename = f"{i:02d}_{safe_title}.png"
                    filepath = os.path.join(downloads_dir, filename)
                    
                    try:
                        # Decode base64 and save as PNG
                        image_bytes = base64.b64decode(image_data)
                        with open(filepath, 'wb') as f:
                            f.write(image_bytes)
                        print(f"   💾 Saved graph to: {filepath}")
                    except Exception as save_error:
                        print(f"   ❌ Failed to save graph: {save_error}")
            else:
                print("❌ No graph generated (returned None)")
                
        except Exception as e:
            print(f"❌ Error generating graph: {e}")
            import traceback
            traceback.print_exc()

async def test_simple_case():
    """Test with a very simple case to check basic functionality"""
    print("\n" + "=" * 60)
    print("SIMPLE TEST CASE")
    print("=" * 60)
    
    generator = UniversalGraphGenerator()
    
    # Create Downloads directory path
    downloads_dir = os.path.expanduser("~/Downloads/graphs")
    os.makedirs(downloads_dir, exist_ok=True)
    
    simple_content = "The demand curve slopes downward from left to right, showing that as price increases, quantity demanded decreases."
    simple_title = "Demand Curve"
    
    print(f"Input content: {simple_content}")
    print(f"Input title: {simple_title}")
    
    try:
        result = await generator.generate_contextual_graph(simple_content, simple_title)
        
        if result:
            print(f"✅ SUCCESS: Graph generated")
            print(f"   Graph type: {result.get('type', 'unknown')}")
            print(f"   Has image data: {'Yes' if result.get('image') else 'No'}")
            
            # Save the simple case graph
            image_data = result.get('image', '')
            if image_data:
                filename = "simple_demand_curve.png"
                filepath = os.path.join(downloads_dir, filename)
                
                try:
                    # Decode base64 and save as PNG
                    image_bytes = base64.b64decode(image_data)
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                    print(f"   💾 Saved simple graph to: {filepath}")
                except Exception as save_error:
                    print(f"   ❌ Failed to save simple graph: {save_error}")
        else:
            print("❌ FAILED: No graph generated")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("Starting UniversalGraphGenerator tests...")
    asyncio.run(test_ai_response())
    print("\n" + "=" * 60)
    asyncio.run(test_graph_generation())
    asyncio.run(test_simple_case())
    print("\nTest completed!")
