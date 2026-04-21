const addBtn = document.getElementById("addPostBtn");
const form = document.querySelector(".news-form");

addBtn.onclick = function(e){
    e.preventDefault();
    form.style.display="block";
}

document.addEventListener("click",function(event){

    if(!form.contains(event.target) && !addBtn.contains(event.target)){
        form.style.display="none";
    }
});

// Toggle comments
function toggleComments(newsId) {
    const section = document.getElementById('comments-section-' + newsId);
    section.style.display = (section.style.display === 'block') ? 'none' : 'block';
}

// Real-time comment submit (AJAX)
function submitComment(newsId) {
    const textarea = document.getElementById('comment-text-' + newsId);
    const text = textarea.value.trim();
    if (!text) return;

    fetch('/api/comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ news_id: newsId, comment_text: text })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const section = document.getElementById('comments-section-' + newsId);
            const newHTML = `
                <div class="comment">
                    <strong>${data.comment.author}</strong> 
                    <small>${data.comment.created_at}</small>
                    <p>${data.comment.comment_text}</p>
                </div>`;
            section.insertAdjacentHTML('beforeend', newHTML);
            textarea.value = '';   // clear box
        }
    });
}

//VOTES
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.vote-btn').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();   // ← stops full page reload

            const votesDiv = this.closest('.votes');
            const newsId   = votesDiv.dataset.newsId;
            const action   = this.dataset.action;

            try {
                const response = await fetch(`/like/${newsId}/${action}`);
                const data = await response.json();

                if (!data.success) {
                    alert(data.message || "Something went wrong");
                    return;
                }

                // Update only the numbers (no reload!)
                votesDiv.querySelector('.like-count').textContent = data.likes;
                votesDiv.querySelector('.dislike-count').textContent = data.dislikes;

                // Optional: small visual feedback
                this.style.transform = 'scale(1.2)';
                setTimeout(() => this.style.transform = 'scale(1)', 200);

            } catch (err) {
                console.error(err);
                alert("Error connecting to server");
            }
        });
    });
});