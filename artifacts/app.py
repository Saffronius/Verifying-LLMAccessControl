"""
Quacky Pipeline Demo - Interactive Web Interface
Demonstrates policy generation, comparison, and analysis using the Quacky tool
"""
import streamlit as st
import json
import os
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.quacky_wrapper import QuackyWrapper
from backend.policy_generator import PolicyGenerator
from backend.regex_synthesizer import RegexSynthesizer

# Page configuration
st.set_page_config(
    page_title="Quacky Pipeline Demo",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'quacky' not in st.session_state:
    st.session_state.quacky = QuackyWrapper()
if 'generator' not in st.session_state:
    st.session_state.generator = PolicyGenerator()
if 'synthesizer' not in st.session_state:
    st.session_state.synthesizer = RegexSynthesizer()
if 'policy1' not in st.session_state:
    st.session_state.policy1 = ""
if 'policy2' not in st.session_state:
    st.session_state.policy2 = ""
if 'generated_strings' not in st.session_state:
    st.session_state.generated_strings = {"p1_not_p2": [], "not_p1_p2": []}
if 'model_preference' not in st.session_state:
    st.session_state.model_preference = "best"
if 'use_reasoning' not in st.session_state:
    st.session_state.use_reasoning = True

# Sidebar navigation
st.sidebar.title("🔐 Quacky Pipeline")
st.sidebar.markdown("---")

# Feature selection
feature = st.sidebar.selectbox(
    "Select Feature",
    ["Policy Generation", "Policy Comparison", "String Generation", "Regex Synthesis", "About"]
)

# Model Configuration Section
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Model Configuration")

# Model preference selection
model_pref = st.sidebar.selectbox(
    "Model Selection",
    ["best", "reasoning", "fast", "legacy"],
    index=0,
    help="""Select model based on your needs:
- **best**: Claude Opus 4.1 / GPT-5 (Most capable, state-of-the-art)
- **reasoning**: Claude Sonnet 4 / O3-Pro (Deep reasoning capabilities)
- **fast**: Claude 3.7 / GPT-5-mini (Quick, efficient)
- **legacy**: Previous generation models"""
)

# Use reasoning checkbox
use_reasoning = st.sidebar.checkbox(
    "Enable Reasoning",
    value=True,
    help="Use step-by-step reasoning for complex tasks (recommended for >50 strings)"
)

# Apply changes button
if st.sidebar.button("Apply Model Settings"):
    st.session_state.model_preference = model_pref
    st.session_state.use_reasoning = use_reasoning
    
    # Reinitialize with new settings
    st.session_state.generator = PolicyGenerator(
        use_reasoning=use_reasoning,
        model_preference=model_pref
    )
    st.session_state.synthesizer = RegexSynthesizer(
        use_reasoning=use_reasoning,
        model_preference=model_pref
    )
    st.sidebar.success("✅ Model settings updated!")

# Display current model info
if st.session_state.generator.model:
    model_name = st.session_state.generator.model
    
    # Task-specific model capabilities
    model_capabilities = {
        "claude-opus-4.1-20250805": {
            "name": "Claude Opus 4.1",
            "strength": "Complex policy analysis",
            "speed": "⚡⚡⚡",
            "accuracy": "★★★★★"
        },
        "claude-sonnet-4-20250523": {
            "name": "Claude Sonnet 4",
            "strength": "Long context policies",
            "speed": "⚡⚡⚡",
            "accuracy": "★★★★★"
        },
        "claude-3.7-sonnet-20250224": {
            "name": "Claude 3.7",
            "strength": "Step-by-step regex",
            "speed": "⚡⚡⚡⚡",
            "accuracy": "★★★★"
        },
        "gpt-5": {
            "name": "GPT-5",
            "strength": "All-around excellence",
            "speed": "⚡⚡⚡",
            "accuracy": "★★★★★"
        },
        "gpt-5-mini": {
            "name": "GPT-5 Mini",
            "strength": "Fast synthesis",
            "speed": "⚡⚡⚡⚡",
            "accuracy": "★★★★"
        },
        "gpt-5-nano": {
            "name": "GPT-5 Nano",
            "strength": "Quick validation",
            "speed": "⚡⚡⚡⚡⚡",
            "accuracy": "★★★"
        },
        "o3-pro": {
            "name": "O3-Pro",
            "strength": "Deep policy reasoning",
            "speed": "⚡⚡",
            "accuracy": "★★★★★"
        },
        "o3": {
            "name": "O3",
            "strength": "Pattern analysis",
            "speed": "⚡⚡",
            "accuracy": "★★★★★"
        },
        "o4-mini": {
            "name": "O4-mini",
            "strength": "Regex optimization",
            "speed": "⚡⚡⚡⚡",
            "accuracy": "★★★★"
        }
    }
    
    if model_name in model_capabilities:
        cap = model_capabilities[model_name]
        st.sidebar.success(f"**Active: {cap['name']}**")
        st.sidebar.markdown(f"💡 {cap['strength']}")
        st.sidebar.markdown(f"Speed: {cap['speed']} | Quality: {cap['accuracy']}")
    else:
        st.sidebar.info(f"**Active:** {model_name}")

# Main content area
st.title("Quacky Pipeline Demonstration")
st.markdown("### Quantitative Analysis of Access Control Policies")

if feature == "Policy Generation":
    st.header("📝 Generate Policy from Natural Language")
    st.markdown("Describe the access control policy you want in plain English, and the system will generate an AWS IAM policy.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Natural Language Description")
        
        # Example prompts
        example = st.selectbox(
            "Example prompts:",
            [
                "Custom prompt...",
                "Allow all EC2 actions in us-west-2 region only",
                "Allow read-only access to S3 buckets starting with 'public-'",
                "Allow Lambda function management but deny deletion",
                "Grant full DynamoDB access except for table deletion"
            ]
        )
        
        if example != "Custom prompt...":
            description = st.text_area(
                "Policy Description:",
                value=example,
                height=150,
                help="Describe the permissions you want to grant or deny"
            )
        else:
            description = st.text_area(
                "Policy Description:",
                placeholder="E.g., Allow users to read from S3 buckets but only in the us-east-1 region",
                height=150,
                help="Describe the permissions you want to grant or deny"
            )
        
        if st.button("🚀 Generate Policy", type="primary"):
            if description:
                with st.spinner("Generating policy..."):
                    result = st.session_state.generator.generate_policy_from_nl(description)
                    
                    if result["success"]:
                        st.session_state.policy1 = result["policy"]
                        st.success(f"✅ Policy generated successfully using {result.get('model_used', 'LLM')}")
                    else:
                        st.error(f"❌ Error: {result['error']}")
                        if result.get("policy"):
                            st.session_state.policy1 = result["policy"]
            else:
                st.warning("Please enter a policy description")
    
    with col2:
        st.subheader("Generated AWS IAM Policy")
        
        if st.session_state.policy1:
            # Display policy with syntax highlighting
            st.code(st.session_state.policy1, language="json")
            
            # Validation
            is_valid, message = st.session_state.quacky.validate_policy(st.session_state.policy1)
            if is_valid:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
            
            # Download button
            st.download_button(
                label="📥 Download Policy",
                data=st.session_state.policy1,
                file_name="generated_policy.json",
                mime="application/json"
            )
            
            # Explain policy
            if st.button("📖 Explain Policy"):
                with st.spinner("Analyzing policy..."):
                    explanation = st.session_state.generator.explain_policy(st.session_state.policy1)
                    if explanation["success"]:
                        st.info(explanation["explanation"])
                    else:
                        st.error(f"Error: {explanation['error']}")
        else:
            st.info("Generated policy will appear here")

elif feature == "Policy Comparison":
    st.header("⚖️ Compare Two Policies")
    st.markdown("Compare two AWS IAM policies to analyze their differences quantitatively.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Policy 1")
        
        # Input method selection
        input_method1 = st.radio(
            "Input method for Policy 1:",
            ["Use Generated", "Paste JSON", "Upload File"],
            key="input1"
        )
        
        if input_method1 == "Use Generated":
            if st.session_state.policy1:
                policy1_text = st.text_area(
                    "Policy 1 JSON:",
                    value=st.session_state.policy1,
                    height=300,
                    key="p1_text"
                )
            else:
                st.info("Generate a policy first in the Policy Generation tab")
                policy1_text = ""
        elif input_method1 == "Paste JSON":
            policy1_text = st.text_area(
                "Policy 1 JSON:",
                placeholder='{"Version": "2012-10-17", "Statement": [...]}',
                height=300,
                key="p1_paste"
            )
        else:  # Upload File
            uploaded_file1 = st.file_uploader(
                "Choose Policy 1 JSON file",
                type=['json'],
                key="p1_upload"
            )
            if uploaded_file1:
                policy1_text = uploaded_file1.read().decode()
                st.code(policy1_text, language="json")
            else:
                policy1_text = ""
    
    with col2:
        st.subheader("Policy 2")
        
        # Input method selection
        input_method2 = st.radio(
            "Input method for Policy 2:",
            ["Paste JSON", "Upload File", "Generate New"],
            key="input2"
        )
        
        if input_method2 == "Generate New":
            nl_description = st.text_area(
                "Describe Policy 2:",
                placeholder="E.g., A more restrictive version of Policy 1",
                height=100,
                key="p2_gen_desc"
            )
            if st.button("Generate Policy 2"):
                if nl_description:
                    with st.spinner("Generating policy..."):
                        result = st.session_state.generator.generate_policy_from_nl(nl_description)
                        if result["success"]:
                            st.session_state.policy2 = result["policy"]
                            st.success("Policy 2 generated successfully")
                        else:
                            st.error(f"Error: {result['error']}")
            
            policy2_text = st.text_area(
                "Policy 2 JSON:",
                value=st.session_state.policy2 if st.session_state.policy2 else "",
                height=200,
                key="p2_gen"
            )
        elif input_method2 == "Paste JSON":
            policy2_text = st.text_area(
                "Policy 2 JSON:",
                placeholder='{"Version": "2012-10-17", "Statement": [...]}',
                height=300,
                key="p2_paste"
            )
        else:  # Upload File
            uploaded_file2 = st.file_uploader(
                "Choose Policy 2 JSON file",
                type=['json'],
                key="p2_upload"
            )
            if uploaded_file2:
                policy2_text = uploaded_file2.read().decode()
                st.code(policy2_text, language="json")
            else:
                policy2_text = ""
    
    # Comparison controls
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        bound = st.slider(
            "Analysis Bound:",
            min_value=10,
            max_value=200,
            value=100,
            step=10,
            help="Higher bounds provide more accurate analysis but take longer"
        )
        
        if st.button("🔍 Compare Policies", type="primary", use_container_width=True):
            if policy1_text and policy2_text:
                # Validate policies
                valid1, msg1 = st.session_state.quacky.validate_policy(policy1_text)
                valid2, msg2 = st.session_state.quacky.validate_policy(policy2_text)
                
                if not valid1:
                    st.error(f"Policy 1 invalid: {msg1}")
                elif not valid2:
                    st.error(f"Policy 2 invalid: {msg2}")
                else:
                    with st.spinner("Analyzing policies with Quacky..."):
                        result = st.session_state.quacky.compare_policies(
                            policy1_text,
                            policy2_text,
                            bound=bound
                        )
                        
                        if result["success"]:
                            st.success("✅ Analysis complete!")
                            
                            # Display metrics
                            st.subheader("📊 Analysis Results")
                            
                            metrics = result.get("metrics", {})
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric(
                                    "Satisfiability",
                                    metrics.get("satisfiability", "N/A")
                                )
                            
                            with col2:
                                st.metric(
                                    "Solve Time",
                                    f"{metrics.get('solve_time_ms', 'N/A')} ms"
                                )
                            
                            with col3:
                                if "log_requests" in metrics:
                                    st.metric(
                                        "Log(Requests)",
                                        f"{metrics['log_requests']:.2f}"
                                    )
                                else:
                                    st.metric("Requests", "0")
                            
                            with col4:
                                if "count_time_ms" in metrics:
                                    st.metric(
                                        "Count Time",
                                        f"{metrics['count_time_ms']} ms"
                                    )
                            
                            # Display raw output
                            with st.expander("📋 Raw Quacky Output"):
                                st.code(result["output"], language="text")
                            
                            if result.get("error"):
                                with st.expander("⚠️ Warnings/Errors"):
                                    st.code(result["error"], language="text")
                            
                            # Interpretation
                            st.subheader("📖 Interpretation")
                            
                            # Check if policies are equivalent (both directions UNSAT)
                            if "Policy 1 and Policy 2 are equivalent" in result.get("output", ""):
                                st.success("**Policies are Equivalent**: Both policies allow exactly the same set of requests")
                            elif metrics.get("satisfiability") == "sat":
                                st.info("**Policy 1 ⇏ Policy 2**: There exist requests allowed by Policy 1 but denied by Policy 2")
                            elif metrics.get("satisfiability") == "unsat":
                                st.success("**Policy 1 ⊆ Policy 2**: All requests allowed by Policy 1 are also allowed by Policy 2")
                            
                        else:
                            st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please provide both policies for comparison")

elif feature == "String Generation":
    st.header("🔤 String Generation")
    st.markdown("Generate example requests that differentiate between policies to understand their differences.")
    
    # Input section
    st.subheader("📥 Input Policies")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Policy 1**")
        input_method1 = st.radio(
            "Input method:",
            ["Use Generated/Stored", "Paste JSON", "Upload File"],
            key="sg_input1"
        )
        
        if input_method1 == "Use Generated/Stored":
            sg_policy1 = st.text_area(
                "Policy 1:",
                value=st.session_state.policy1 if st.session_state.policy1 else "",
                height=200,
                key="sg_p1_stored"
            )
        elif input_method1 == "Paste JSON":
            sg_policy1 = st.text_area(
                "Policy 1:",
                placeholder='{"Version": "2012-10-17", "Statement": [...]}',
                height=200,
                key="sg_p1_paste"
            )
        else:
            uploaded = st.file_uploader("Upload Policy 1", type=['json'], key="sg_p1_upload")
            sg_policy1 = uploaded.read().decode() if uploaded else ""
    
    with col2:
        st.markdown("**Policy 2 (Optional)**")
        use_policy2 = st.checkbox("Compare with Policy 2", value=True)
        
        if use_policy2:
            input_method2 = st.radio(
                "Input method:",
                ["Use Generated/Stored", "Paste JSON", "Upload File"],
                key="sg_input2"
            )
            
            if input_method2 == "Use Generated/Stored":
                sg_policy2 = st.text_area(
                    "Policy 2:",
                    value=st.session_state.policy2 if st.session_state.policy2 else "",
                    height=200,
                    key="sg_p2_stored"
                )
            elif input_method2 == "Paste JSON":
                sg_policy2 = st.text_area(
                    "Policy 2:",
                    placeholder='{"Version": "2012-10-17", "Statement": [...]}',
                    height=200,
                    key="sg_p2_paste"
                )
            else:
                uploaded = st.file_uploader("Upload Policy 2", type=['json'], key="sg_p2_upload")
                sg_policy2 = uploaded.read().decode() if uploaded else ""
        else:
            sg_policy2 = None
    
    # Generation parameters
    st.markdown("---")
    st.subheader("⚙️ Generation Parameters")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        num_strings = st.number_input(
            "Number of strings to generate:",
            min_value=1,
            max_value=2000,
            value=10,
            step=5
        )
    
    with col2:
        min_range = st.number_input(
            "Minimum string length:",
            min_value=1,
            max_value=50,
            value=5
        )
    
    with col3:
        max_range = st.number_input(
            "Maximum string length:",
            min_value=min_range,
            max_value=100,
            value=20
        )
    
    # Generate button
    if st.button("🎯 Generate Strings", type="primary", use_container_width=True):
        if sg_policy1:
            # Validate policies
            valid1, msg1 = st.session_state.quacky.validate_policy(sg_policy1)
            if not valid1:
                st.error(f"Policy 1 invalid: {msg1}")
            else:
                if sg_policy2:
                    valid2, msg2 = st.session_state.quacky.validate_policy(sg_policy2)
                    if not valid2:
                        st.error(f"Policy 2 invalid: {msg2}")
                        sg_policy2 = None
                
                with st.spinner("Generating example strings..."):
                    result = st.session_state.quacky.generate_strings(
                        sg_policy1,
                        sg_policy2,
                        count=num_strings,
                        min_range=min_range,
                        max_range=max_range
                    )
                    
                    if result["success"]:
                        st.success("✅ Strings generated successfully!")
                        st.session_state.generated_strings = {
                            "p1_not_p2": result["p1_not_p2"],
                            "not_p1_p2": result["not_p1_p2"]
                        }
                    else:
                        st.error(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please provide at least Policy 1")
    
    # Display results
    if st.session_state.generated_strings["p1_not_p2"] or st.session_state.generated_strings["not_p1_p2"]:
        st.markdown("---")
        st.subheader("📊 Generated Strings")
        
        if use_policy2 and sg_policy2:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Allowed by Policy 1 but NOT Policy 2** (P1 \\ P2)")
                if st.session_state.generated_strings["p1_not_p2"]:
                    strings_text = "\n".join(st.session_state.generated_strings["p1_not_p2"])
                    st.text_area(
                        "P1_not_P2 strings:",
                        value=strings_text,
                        height=300,
                        key="p1_not_p2_display"
                    )
                    st.download_button(
                        "📥 Download P1_not_P2",
                        data=strings_text,
                        file_name="P1_not_P2.txt",
                        mime="text/plain"
                    )
                else:
                    st.info("No strings found (policies might be equivalent)")
            
            with col2:
                st.markdown("**Allowed by Policy 2 but NOT Policy 1** (P2 \\ P1)")
                if st.session_state.generated_strings["not_p1_p2"]:
                    strings_text = "\n".join(st.session_state.generated_strings["not_p1_p2"])
                    st.text_area(
                        "not_P1_P2 strings:",
                        value=strings_text,
                        height=300,
                        key="not_p1_p2_display"
                    )
                    st.download_button(
                        "📥 Download not_P1_P2",
                        data=strings_text,
                        file_name="not_P1_P2.txt",
                        mime="text/plain"
                    )
                else:
                    st.info("No strings found (policies might be equivalent)")
        else:
            st.markdown("**Strings allowed by Policy 1**")
            if st.session_state.generated_strings["p1_not_p2"]:
                strings_text = "\n".join(st.session_state.generated_strings["p1_not_p2"])
                st.text_area(
                    "Generated strings:",
                    value=strings_text,
                    height=300,
                    key="p1_strings_display"
                )
                st.download_button(
                    "📥 Download Strings",
                    data=strings_text,
                    file_name="policy1_strings.txt",
                    mime="text/plain"
                )
        
        # Statistics
        st.subheader("📈 Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("P1 \\ P2 Strings", len(st.session_state.generated_strings["p1_not_p2"]))
        with col2:
            st.metric("P2 \\ P1 Strings", len(st.session_state.generated_strings["not_p1_p2"]))
        with col3:
            total = len(st.session_state.generated_strings["p1_not_p2"]) + len(st.session_state.generated_strings["not_p1_p2"])
            st.metric("Total Generated", total)

elif feature == "Regex Synthesis":
    st.header("🔍 Regex Synthesis & Validation")
    st.markdown("Synthesize regex patterns from example strings and validate them against policies.")
    
    # Tab selection
    tab1, tab2, tab3, tab4 = st.tabs(["Synthesize Regex", "Validate Against Policy", "Regex Comparison", "Regex Tools"])
    
    with tab1:
        st.subheader("🎯 Synthesize Regex from Strings")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Input Example Strings**")
            
            input_method = st.radio(
                "Input method:",
                ["Use Generated Strings", "Paste Examples", "Upload File"],
                key="regex_input"
            )
            
            if input_method == "Use Generated Strings":
                string_set = st.selectbox(
                    "Select string set:",
                    ["P1_not_P2", "not_P1_P2"]
                )
                
                if string_set == "P1_not_P2":
                    example_strings = st.session_state.generated_strings["p1_not_p2"]
                else:
                    example_strings = st.session_state.generated_strings["not_p1_p2"]
                
                if example_strings:
                    strings_text = "\n".join(example_strings)
                    st.text_area(
                        "Example strings:",
                        value=strings_text,
                        height=250,
                        key="regex_generated_strings"
                    )
                else:
                    st.info("No generated strings available. Generate strings first in the String Generation tab.")
                    strings_text = ""
            
            elif input_method == "Paste Examples":
                strings_text = st.text_area(
                    "Enter example strings (one per line):",
                    placeholder="ec2:DescribeInstances:us-west-2:123456789012\nec2:RunInstances:us-west-2:123456789012\nec2:TerminateInstances:us-west-2:123456789012",
                    height=250,
                    key="regex_paste_strings"
                )
                example_strings = [s.strip() for s in strings_text.split('\n') if s.strip()]
            
            else:  # Upload File
                uploaded = st.file_uploader(
                    "Upload text file with strings (one per line)",
                    type=['txt', 'models'],
                    key="regex_upload"
                )
                if uploaded:
                    strings_text = uploaded.read().decode()
                    example_strings = [s.strip() for s in strings_text.split('\n') if s.strip()]
                    st.text_area(
                        "Uploaded strings:",
                        value=strings_text,
                        height=250,
                        key="regex_uploaded_strings"
                    )
                else:
                    example_strings = []
                    strings_text = ""
            
            # Show string count info
            if example_strings:
                max_synthesis_strings = 500
                strings_to_use = min(len(example_strings), max_synthesis_strings)
                st.info(f"📊 Using {strings_to_use} out of {len(example_strings)} strings for synthesis (max: {max_synthesis_strings})")
                
                # Show if reasoning will be used
                if st.session_state.use_reasoning and strings_to_use > 50:
                    st.info("🧠 Reasoning mode will be activated for enhanced pattern analysis")
            
            # Synthesis button
            if st.button("🔮 Synthesize Regex", type="primary"):
                if example_strings:
                    reasoning_msg = " with reasoning" if (st.session_state.use_reasoning and len(example_strings) > 50) else ""
                    with st.spinner(f"Synthesizing regex pattern from {min(len(example_strings), 500)} strings{reasoning_msg}..."):
                        result = st.session_state.synthesizer.synthesize_regex(example_strings)
                        
                        if result["success"]:
                            st.session_state.synthesized_regex = result["regex"]
                            st.session_state.synthesis_result = result  # Store full result for details
                            st.success(f"✅ Regex synthesized using {result['model_used']}")
                            
                            # Display synthesis details
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Strings Provided", result.get("num_examples", 0))
                            with col2:
                                st.metric("Strings Used", result.get("num_used_for_synthesis", 0))
                            with col3:
                                if result.get("used_reasoning", False):
                                    st.metric("Method", "🧠 Reasoning")
                                else:
                                    st.metric("Method", "⚡ Direct")
                        else:
                            st.error(f"❌ Synthesis failed: {result['error']}")
                else:
                    st.warning("Please provide example strings")
        
        with col2:
            st.markdown("**Synthesized Regex Pattern**")
            
            if 'synthesized_regex' in st.session_state and st.session_state.synthesized_regex:
                # Display regex
                st.code(st.session_state.synthesized_regex, language="regex")
                
                # Copy button
                st.text_input(
                    "Copy regex:",
                    value=st.session_state.synthesized_regex,
                    key="regex_copy"
                )
                
                # Download button
                st.download_button(
                    "📥 Download Regex",
                    data=st.session_state.synthesized_regex,
                    file_name="synthesized_regex.txt",
                    mime="text/plain"
                )
                
                # Explain regex
                if st.button("📖 Explain Regex"):
                    with st.spinner("Analyzing regex..."):
                        explanation = st.session_state.synthesizer.explain_regex(
                            st.session_state.synthesized_regex
                        )
                        if explanation["success"]:
                            st.info(explanation["explanation"])
                        else:
                            st.error(f"Error: {explanation['error']}")
                
                # Test matches
                st.markdown("**Test Regex Matches**")
                test_string = st.text_input(
                    "Test string:",
                    placeholder="Enter a string to test against the regex"
                )
                
                if test_string:
                    import re
                    try:
                        if re.match(st.session_state.synthesized_regex, test_string):
                            st.success(f"✅ '{test_string}' matches the regex")
                        else:
                            st.error(f"❌ '{test_string}' does not match the regex")
                    except re.error as e:
                        st.error(f"Invalid regex: {e}")
            else:
                st.info("Synthesized regex will appear here")
    
    with tab2:
        st.subheader("✅ Validate Regex Against Policy")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Policy to Validate Against**")
            
            policy_input = st.radio(
                "Policy input:",
                ["Use Stored Policy", "Paste JSON", "Upload File"],
                key="regex_val_policy"
            )
            
            if policy_input == "Use Stored Policy":
                val_policy = st.text_area(
                    "Policy:",
                    value=st.session_state.policy1 if st.session_state.policy1 else "",
                    height=200,
                    key="regex_val_stored"
                )
            elif policy_input == "Paste JSON":
                val_policy = st.text_area(
                    "Policy JSON:",
                    placeholder='{"Version": "2012-10-17", "Statement": [...]}',
                    height=200,
                    key="regex_val_paste"
                )
            else:
                uploaded = st.file_uploader(
                    "Upload Policy",
                    type=['json'],
                    key="regex_val_upload"
                )
                val_policy = uploaded.read().decode() if uploaded else ""
            
            st.markdown("**Regex Pattern to Validate**")
            
            regex_to_validate = st.text_area(
                "Regex pattern:",
                value=st.session_state.synthesized_regex if 'synthesized_regex' in st.session_state else "",
                height=100,
                key="regex_to_validate"
            )
        
        with col2:
            st.markdown("**Validation Parameters**")
            
            validation_bound = st.slider(
                "Analysis bound:",
                min_value=10,
                max_value=200,
                value=100,
                step=10,
                key="regex_val_bound"
            )
            
            if st.button("🔍 Validate Regex", type="primary"):
                if val_policy and regex_to_validate:
                    valid, msg = st.session_state.quacky.validate_policy(val_policy)
                    if not valid:
                        st.error(f"Policy invalid: {msg}")
                    else:
                        with st.spinner("Validating regex against policy..."):
                            result = st.session_state.quacky.validate_regex(
                                val_policy,
                                regex_to_validate,
                                bound=validation_bound
                            )
                            
                            if result["success"]:
                                st.success("✅ Validation complete!")
                                
                                # Store the validation results in session state for comparison tab
                                st.session_state.validation_metrics = result.get("metrics", {})
                                st.session_state.validation_output = result.get("output", "")
                                
                                st.markdown("**Validation Results**")
                                
                                metrics = result.get("metrics", {})
                                
                                # Display basic metrics
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    if "baseline_regex" in metrics:
                                        st.metric("Baseline Count", metrics["baseline_regex"])
                                
                                with col2:
                                    if "synthesized_regex" in metrics:
                                        st.metric("Synthesized Count", metrics["synthesized_regex"])
                                
                                with col3:
                                    if "jaccard_similarity" in metrics:
                                        st.metric("Jaccard Similarity", f"{metrics['jaccard_similarity']:.2%}")
                                
                                # Show regex comparison if available
                                if "regex_from_dfa" in metrics:
                                    st.markdown("**📊 Regex Comparison Available**")
                                    st.info("Switch to the 'Regex Comparison' tab to see detailed analysis of the automata-generated regex vs the simplified version.")
                                
                                if "abc_command" in metrics:
                                    with st.expander("🔧 ABC Command"):
                                        st.code(metrics["abc_command"], language="bash")
                                
                                with st.expander("📋 Raw Output"):
                                    st.code(result["output"], language="text")
                            else:
                                st.error(f"❌ Validation failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please provide both policy and regex pattern")
    
    with tab3:
        st.subheader("📊 Regex Comparison & Simplification Analysis")
        
        if 'validation_metrics' not in st.session_state or not st.session_state.validation_metrics:
            st.info("👆 First validate a regex against a policy in the 'Validate Against Policy' tab to see comparison data.")
        else:
            metrics = st.session_state.validation_metrics
            
            # Check if we have both regex versions
            if "regex_from_dfa" in metrics and "regex_from_llm" in metrics:
                st.markdown("### 🤖 Automata vs LLM Regex Comparison")
                
                # Display both regex patterns
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**🔧 Non-Simplified Regex (from Automata/DFA)**")
                    st.text_area(
                        "Automata Regex:",
                        value=metrics["regex_from_dfa"],
                        height=200,
                        key="dfa_regex_display",
                        help="This is the raw regex extracted directly from the DFA/automata"
                    )
                    
                    # Metrics for DFA regex
                    st.markdown("**Metrics:**")
                    if "length_regex_from_dfa" in metrics:
                        st.metric("Length", metrics["length_regex_from_dfa"])
                    if "ops_regex_from_dfa" in metrics:
                        st.metric("Operations Count", metrics["ops_regex_from_dfa"])
                
                with col2:
                    st.markdown("**✨ Simplified Regex (from LLM)**")
                    st.text_area(
                        "LLM Simplified Regex:",
                        value=metrics["regex_from_llm"],
                        height=200,
                        key="llm_regex_display",
                        help="This is the simplified version generated by the LLM"
                    )
                    
                    # Metrics for LLM regex
                    st.markdown("**Metrics:**")
                    if "length_regex_from_llm" in metrics:
                        st.metric("Length", metrics["length_regex_from_llm"])
                    if "ops_regex_from_llm" in metrics:
                        st.metric("Operations Count", metrics["ops_regex_from_llm"])
                
                # Similarity and Simplification Metrics
                st.markdown("---")
                st.markdown("### 📈 Simplification Effectiveness")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if "jaccard_similarity" in metrics:
                        similarity_pct = metrics["jaccard_similarity"] * 100
                        st.metric(
                            "Jaccard Similarity",
                            f"{similarity_pct:.2f}%",
                            help="Measures the overlap between strings matched by both regex patterns"
                        )
                
                with col2:
                    if "length_reduction_pct" in metrics:
                        st.metric(
                            "Length Reduction",
                            f"{metrics['length_reduction_pct']:.1f}%",
                            help="Percentage reduction in regex length after simplification"
                        )
                
                with col3:
                    if "ops_reduction_pct" in metrics:
                        st.metric(
                            "Operations Reduction",
                            f"{metrics['ops_reduction_pct']:.1f}%",
                            help="Percentage reduction in regex operations after simplification"
                        )
                
                with col4:
                    # Calculate complexity score
                    if "length_regex_from_dfa" in metrics and "length_regex_from_llm" in metrics:
                        complexity_ratio = metrics["length_regex_from_llm"] / metrics["length_regex_from_dfa"]
                        if complexity_ratio < 0.2:
                            complexity_label = "Excellent"
                            complexity_color = "🟢"
                        elif complexity_ratio < 0.5:
                            complexity_label = "Good"
                            complexity_color = "🟡"
                        else:
                            complexity_label = "Moderate"
                            complexity_color = "🟠"
                        st.metric(
                            "Simplification",
                            f"{complexity_color} {complexity_label}",
                            help="Overall assessment of simplification quality"
                        )
                
                # Detailed Analysis
                st.markdown("---")
                st.markdown("### 🔍 Detailed Analysis")
                
                with st.expander("📊 Jaccard Index Explanation"):
                    st.markdown("""
                    The **Jaccard Similarity Index** measures the similarity between the sets of strings matched by the two regex patterns:
                    
                    - **100%**: Both regex patterns match exactly the same set of strings
                    - **>80%**: Very high similarity, minor differences
                    - **50-80%**: Moderate similarity, some notable differences
                    - **<50%**: Low similarity, significant differences
                    
                    The similarity is calculated as: `|A ∩ B| / |A ∪ B|`
                    where A is the set matched by the DFA regex and B is the set matched by the LLM regex.
                    """)
                    
                    if "jaccard_numerator" in metrics and "jaccard_denominator" in metrics:
                        st.markdown(f"""
                        **Your Results:**
                        - Intersection size: {metrics['jaccard_numerator']}
                        - Union size: {metrics['jaccard_denominator']}
                        - Similarity: {metrics.get('jaccard_similarity', 0):.4f}
                        """)
                
                with st.expander("📉 Simplification Metrics"):
                    st.markdown("""
                    **Length Reduction**: How much shorter the simplified regex is compared to the original.
                    - Higher percentage = better simplification
                    - Typical good range: 60-90% reduction
                    
                    **Operations Reduction**: How many fewer regex operations the simplified version uses.
                    - Each character class, alternation, repetition counts as an operation
                    - Fewer operations = easier to understand and faster to execute
                    """)
                    
                    if "length_regex_from_dfa" in metrics and "length_regex_from_llm" in metrics:
                        st.markdown(f"""
                        **Your Results:**
                        - Original length: {metrics['length_regex_from_dfa']} characters
                        - Simplified length: {metrics['length_regex_from_llm']} characters
                        - Reduction: {metrics.get('length_reduction_pct', 0):.1f}%
                        """)
                
                # Download comparison report
                st.markdown("---")
                comparison_report = f"""Regex Comparison Report
=====================================

Non-Simplified Regex (from Automata):
{metrics.get('regex_from_dfa', 'N/A')}

Simplified Regex (from LLM):
{metrics.get('regex_from_llm', 'N/A')}

Metrics:
--------
Jaccard Similarity: {metrics.get('jaccard_similarity', 0):.4f}
Length Reduction: {metrics.get('length_reduction_pct', 0):.1f}%
Operations Reduction: {metrics.get('ops_reduction_pct', 0):.1f}%

Original Length: {metrics.get('length_regex_from_dfa', 'N/A')}
Simplified Length: {metrics.get('length_regex_from_llm', 'N/A')}
Original Operations: {metrics.get('ops_regex_from_dfa', 'N/A')}
Simplified Operations: {metrics.get('ops_regex_from_llm', 'N/A')}
"""
                
                st.download_button(
                    "📥 Download Comparison Report",
                    data=comparison_report,
                    file_name="regex_comparison_report.txt",
                    mime="text/plain"
                )
            
            elif "regex_from_dfa" in metrics:
                # Only have DFA regex
                st.markdown("### 🔧 Automata-Generated Regex")
                st.text_area(
                    "Regex from DFA:",
                    value=metrics["regex_from_dfa"],
                    height=200,
                    key="dfa_only_display"
                )
                st.info("ℹ️ No simplified version available for comparison. The LLM simplification may not have been generated.")
            else:
                st.warning("⚠️ No regex comparison data available. The validation may not have included regex extraction.")
    
    with tab4:
        st.subheader("🛠️ Regex Tools")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Optimize Regex**")
            
            regex_to_optimize = st.text_area(
                "Current regex:",
                placeholder="Enter a regex pattern to optimize",
                height=100,
                key="regex_optimize_input"
            )
            
            if st.button("⚡ Optimize"):
                if regex_to_optimize:
                    # Use example strings if available
                    example_strings = st.session_state.generated_strings.get("p1_not_p2", [])
                    max_opt_strings = 100
                    strings_for_opt = example_strings[:max_opt_strings] if example_strings else []
                    
                    if strings_for_opt:
                        st.info(f"Using {len(strings_for_opt)} example strings for optimization context")
                    
                    with st.spinner("Optimizing regex..."):
                        result = st.session_state.synthesizer.optimize_regex(
                            regex_to_optimize,
                            strings_for_opt
                        )
                        
                        if result["success"]:
                            st.success("✅ Optimization complete!")
                            st.markdown("**Optimized regex:**")
                            st.code(result["optimized"], language="regex")
                            
                            if result["optimized"] != result["original"]:
                                st.info("The regex has been optimized for better performance or readability")
                            else:
                                st.info("The regex is already optimal")
                        else:
                            st.error(f"Error: {result['error']}")
                else:
                    st.warning("Please provide a regex pattern to optimize")
        
        with col2:
            st.markdown("**Regex Tester**")
            
            test_regex = st.text_input(
                "Regex pattern:",
                placeholder="Enter regex pattern",
                key="regex_test_pattern"
            )
            
            test_strings_input = st.text_area(
                "Test strings (one per line):",
                placeholder="string1\nstring2\nstring3",
                height=150,
                key="regex_test_strings"
            )
            
            if st.button("🧪 Test All"):
                if test_regex and test_strings_input:
                    import re
                    try:
                        pattern = re.compile(test_regex)
                        test_strings = [s.strip() for s in test_strings_input.split('\n') if s.strip()]
                        
                        results = []
                        for s in test_strings:
                            match = bool(pattern.match(s))
                            results.append((s, match))
                        
                        st.markdown("**Test Results:**")
                        for string, matched in results:
                            if matched:
                                st.success(f"✅ `{string}`")
                            else:
                                st.error(f"❌ `{string}`")
                        
                        # Summary
                        matches = sum(1 for _, m in results if m)
                        st.info(f"Matched {matches}/{len(results)} strings")
                        
                    except re.error as e:
                        st.error(f"Invalid regex: {e}")
                else:
                    st.warning("Please provide both regex and test strings")

else:  # About
    st.header("ℹ️ About Quacky Pipeline")
    
    st.markdown("""
    ### What is Quacky?
    
    Quacky is a tool for **quantitative analysis of access control policies**. It uses formal methods 
    (SMT solving and model counting) to precisely analyze and compare security policies.
    
    ### Key Features
    
    1. **Policy Generation** - Convert natural language descriptions into formal AWS IAM policies
    2. **Policy Comparison** - Quantitatively compare two policies to find differences
    3. **String Generation** - Generate example requests that distinguish between policies
    4. **Regex Synthesis** - Create patterns that match policy-allowed requests
    5. **Validation** - Verify regex patterns against policies
    
    ### How It Works
    
    1. Policies are translated to SMT-LIB formulas
    2. The ABC solver performs model counting
    3. Results show the space of allowed/denied requests
    4. Differences are quantified precisely
    
    ### Use Cases
    
    - **Security Auditing** - Find unintended permissions
    - **Policy Migration** - Ensure consistency when updating policies
    - **Compliance** - Verify policies meet requirements
    - **Testing** - Generate test cases for access control
    
    ### Technical Stack
    
    - **Backend**: Quacky (Python) with ABC solver
    - **LLM Integration**: Claude/GPT for NL processing
    - **Frontend**: Streamlit for interactive UI
    - **Analysis**: SMT-LIB and automata-based counting
    """)
    
    # Display example workflow
    st.subheader("📋 Example Workflow")
    st.code("""
    1. Describe policy in natural language
       → "Allow EC2 actions in us-west-2 only"
    
    2. Generate formal AWS IAM policy
       → {"Statement": [{"Effect": "Allow", ...}]}
    
    3. Compare with another policy
       → Quantify differences: 2^48 different requests
    
    4. Generate distinguishing examples
       → ec2:CreateInstance in us-east-1 (denied)
    
    5. Synthesize regex for allowed patterns
       → ec2:.*:us-west-2:.*
    """, language="text")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ Configuration")
if st.sidebar.button("Check Setup"):
    checks = []
    
    # Check Quacky
    if os.path.exists("/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"):
        checks.append("✅ Quacky found")
    else:
        checks.append("❌ Quacky not found")
    
    # Check ABC
    if os.system("which abc > /dev/null 2>&1") == 0:
        checks.append("✅ ABC solver found")
    else:
        checks.append("❌ ABC solver not found")
    
    # Check API keys
    if st.session_state.generator.client:
        checks.append(f"✅ LLM API configured ({st.session_state.generator.provider})")
    else:
        checks.append("❌ No LLM API key found")
    
    for check in checks:
        st.sidebar.write(check)

st.sidebar.markdown("---")
st.sidebar.caption("Quacky Pipeline Demo v1.0")