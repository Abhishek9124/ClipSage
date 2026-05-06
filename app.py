import streamlit as st

from supporting_functions import (
    extract_video_id,
    fetch_transcript_segments,
    segments_to_text,
    segments_to_timestamped_text,
    translate_transcript,
    generate_notes,
    get_important_topics,
    generate_quiz,
    generate_flashcards,
    extract_key_quotes,
    analyze_sentiment,
    generate_blog_post,
    generate_linkedin_post,
    generate_twitter_thread,
    generate_mindmap_structure,
    render_mindmap_html,
    create_chunks,
    create_vector_store,
    rag_answer,
    linkify_timestamps,
    export_markdown,
    export_docx,
    export_pdf,
)

st.set_page_config(page_title="ClipSage", page_icon="🎬", layout="wide")


def reset_chat():
    st.session_state.messages = []


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


# --- Sidebar ---
with st.sidebar:
    st.title("🎬 ClipSage")
    st.caption("AI-powered YouTube content synthesizer")
    st.markdown("Transform any YouTube video into notes, quizzes, posts, or a chatbot.")
    st.markdown("---")
    st.markdown("### Input")

    youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    language = st.text_input(
        "Language code (or 'auto')",
        value="auto",
        help="Use 'auto' to auto-detect, or e.g. en, hi, es, fr",
    )
    target_lang = st.text_input("Output language", value="English")

    task_option = st.radio(
        "Task:",
        [
            "Notes For You",
            "Chat with Video",
            "Quiz / Flashcards",
            "Key Quotes",
            "Sentiment & Tone",
            "Blog Post",
            "LinkedIn Post",
            "Twitter Thread",
            "Mind Map",
        ],
    )

    note_length = st.select_slider(
        "Notes length", options=["Short", "Medium", "Detailed"], value="Medium"
    )

    submit_button = st.button("✨ Start Processing", use_container_width=True)
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 New Chat", use_container_width=True):
            reset_chat()
    with col_b:
        if st.button("🧹 Reset All", use_container_width=True):
            reset_all()
            st.rerun()


# --- Main ---
st.title("ClipSage — AI-powered YouTube content synthesizer")
st.caption("Paste a video link and pick a task from the sidebar.")


def export_buttons(title: str, content: str, key_prefix: str):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "⬇️ Markdown",
            data=export_markdown(title, content),
            file_name=f"{key_prefix}.md",
            mime="text/markdown",
            key=f"md_{key_prefix}",
            use_container_width=True,
        )
    with c2:
        try:
            st.download_button(
                "⬇️ DOCX",
                data=export_docx(title, content),
                file_name=f"{key_prefix}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"docx_{key_prefix}",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"DOCX unavailable: {e}")
    with c3:
        try:
            st.download_button(
                "⬇️ PDF",
                data=export_pdf(title, content),
                file_name=f"{key_prefix}.pdf",
                mime="application/pdf",
                key=f"pdf_{key_prefix}",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"PDF unavailable: {e}")


# --- Processing ---
if submit_button and youtube_url:
    video_id = extract_video_id(youtube_url)
    if video_id:
        progress = st.progress(0, text="Fetching transcript...")
        segments, lang_used = fetch_transcript_segments(video_id, language)

        if not segments:
            st.stop()

        progress.progress(25, text=f"Transcript fetched (language: {lang_used}).")
        raw_text = segments_to_text(segments)
        ts_text = segments_to_timestamped_text(segments)

        if target_lang.strip().lower() != "english" or lang_used != "en":
            progress.progress(40, text=f"Translating to {target_lang}...")
            raw_text = translate_transcript(raw_text, target_lang)

        st.session_state.video_id = video_id
        st.session_state.raw_text = raw_text
        st.session_state.ts_text = ts_text
        st.session_state.task = task_option

        progress.progress(60, text="Running task...")

        if task_option == "Notes For You":
            topics = get_important_topics(raw_text)
            notes = generate_notes(ts_text, note_length)
            notes = linkify_timestamps(notes, video_id)
            st.session_state.result = {"topics": topics, "notes": notes}

        elif task_option == "Chat with Video":
            chunks = create_chunks(raw_text)
            st.session_state.vector_store = create_vector_store(chunks, video_id)
            st.session_state.messages = []

        elif task_option == "Quiz / Flashcards":
            quiz = generate_quiz(raw_text, 5)
            cards = generate_flashcards(raw_text, 10)
            st.session_state.result = {"quiz": quiz, "cards": cards}

        elif task_option == "Key Quotes":
            quotes = extract_key_quotes(ts_text, 7)
            st.session_state.result = {"quotes": linkify_timestamps(quotes, video_id)}

        elif task_option == "Sentiment & Tone":
            st.session_state.result = {"sentiment": analyze_sentiment(raw_text)}

        elif task_option == "Blog Post":
            st.session_state.result = {"blog": generate_blog_post(raw_text)}

        elif task_option == "LinkedIn Post":
            st.session_state.result = {"linkedin": generate_linkedin_post(raw_text)}

        elif task_option == "Twitter Thread":
            st.session_state.result = {"twitter": generate_twitter_thread(raw_text)}

        elif task_option == "Mind Map":
            structure = generate_mindmap_structure(raw_text)
            html = render_mindmap_html(structure)
            st.session_state.result = {"mindmap_html": html, "mindmap_struct": structure}

        progress.progress(100, text="Done.")
        progress.empty()
        st.success(f"✅ {task_option} generated.")


# --- Display Results ---
result = st.session_state.get("result")
task = st.session_state.get("task")
video_id = st.session_state.get("video_id")

if result and task:
    if task == "Notes For You":
        st.subheader("📌 Important Topics")
        st.markdown(result["topics"])
        st.markdown("---")
        st.subheader("📝 Notes")
        st.markdown(result["notes"], unsafe_allow_html=False)
        export_buttons("Video Notes", f"## Topics\n{result['topics']}\n\n## Notes\n{result['notes']}", "notes")

    elif task == "Quiz / Flashcards":
        tab1, tab2 = st.tabs(["Quiz", "Flashcards"])
        with tab1:
            st.markdown(result["quiz"])
            export_buttons("Quiz", result["quiz"], "quiz")
        with tab2:
            st.markdown(result["cards"])
            export_buttons("Flashcards", result["cards"], "flashcards")

    elif task == "Key Quotes":
        st.subheader("💬 Key Quotes")
        st.markdown(result["quotes"])
        export_buttons("Key Quotes", result["quotes"], "quotes")

    elif task == "Sentiment & Tone":
        st.subheader("🎭 Sentiment & Tone")
        st.markdown(result["sentiment"])
        export_buttons("Sentiment Analysis", result["sentiment"], "sentiment")

    elif task == "Blog Post":
        st.subheader("✍️ Blog Post")
        st.markdown(result["blog"])
        export_buttons("Blog Post", result["blog"], "blog")

    elif task == "LinkedIn Post":
        st.subheader("💼 LinkedIn Post")
        st.markdown(result["linkedin"])
        export_buttons("LinkedIn Post", result["linkedin"], "linkedin")

    elif task == "Twitter Thread":
        st.subheader("🐦 Twitter Thread")
        st.markdown(result["twitter"])
        export_buttons("Twitter Thread", result["twitter"], "twitter")

    elif task == "Mind Map":
        import streamlit.components.v1 as components
        st.subheader("🧠 Mind Map")
        components.html(result["mindmap_html"], height=680, scrolling=False)
        st.download_button(
            "⬇️ Download Mind Map (HTML)",
            data=result["mindmap_html"].encode("utf-8"),
            file_name="mindmap.html",
            mime="text/html",
            key="mindmap_html_dl",
        )
        with st.expander("View as outline"):
            s = result["mindmap_struct"]
            st.markdown(f"### {s.get('central', '')}")
            for b in s.get("branches", []):
                st.markdown(f"- **{b.get('title', '')}**")
                for c in b.get("children", []):
                    st.markdown(f"    - {c}")


# --- Chat ---
if task_option == "Chat with Video" and "vector_store" in st.session_state:
    st.divider()
    st.subheader("💬 Chat with Video")

    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ask anything about the video.")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = rag_answer(prompt, st.session_state.vector_store)
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
