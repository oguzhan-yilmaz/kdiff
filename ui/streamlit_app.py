import streamlit as st

# Define the pages
main_page = st.Page("pages/mainpage.py", title="Home")  # , icon="🎈"
take_a_diff = st.Page("pages/take_a_diff.py", title="Page 2", icon="❄️")
abc = st.Page("pages/queryparam.py", title="queryparam", icon="🎉")
snapshot_list = st.Page("pages/snapshot_list.py", title="snapshot_list", icon="🎉")
mcontext = st.Page("pages/multi-context.py", title="multi-context", icon="🎉")
diff_context = st.Page("pages/diff-multi-context.py", title="diff-multi-context", icon="🎉")
 

# Set up navigation
# pg = st.navigation([main_page, page_2, page_3])
pg = st.navigation([main_page, take_a_diff,abc,snapshot_list, mcontext, diff_context])

# Run the selected page
pg.run()