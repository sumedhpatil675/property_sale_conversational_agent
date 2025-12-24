from langchain_core.prompts import ChatPromptTemplate

BOOK_PROMPT = ChatPromptTemplate.from_template("""
    You are an extraction assistant.
    Extract the following booking details from the conversation history and the latest user input:
    - Lead Name (name)
    - Lead Email (email)
    - Project Name (project)
    - City (city)
    
    Conversation History:
    {history}
    
    Latest User Input: {text}
    
    Instructions:
    - Look for name and email in the history if not present in the latest input.
    - If the user says "Book it" or "I'm interested", look for the project name mentioned in the immediately preceding Assistant message or User message.
    - If no specific project name is mentioned, extract the property description (e.g. "1 bedroom apartment in Dubai Marina") as the 'project'.
    - If the user refers to "the project in [Location]", extract [Location] as the 'project' if no specific project name is mentioned.
    - If the user provides only one piece of info (e.g. name), keep the others as null.
    
    Return a valid JSON object with keys: name, email, project, city. 
    Values should be null if not found.
    Do NOT include markdown formatting like ```json ... ```. Just the raw JSON string.
""")
