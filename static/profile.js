// Load saved image from localStorage on page load
    function loadProfilePic() {
        const savedImage = localStorage.getItem('profilePic');
        const imgElement = document.getElementById('profilePic');
            
        if (savedImage) {
            imgElement.src = savedImage;
            console.log('%c✅ Profile image loaded from localStorage', 'color:#00d4ff;font-weight:bold');
        } else {
            // Beautiful default avatar (base64 embedded - no external dependency)
            imgElement.src = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Ccircle cx='100' cy='100' r='90' fill='%231a1a2e'/%3E%3Ccircle cx='100' cy='70' r='30' fill='%2300d4ff'/%3E%3Cpath d='M40 140 Q100 180 160 140' stroke='%2300d4ff' stroke-width='25' fill='none'/%3E%3C/svg%3E`;
            console.log('%c🖼️ Using default avatar', 'color:#aaa');
        }
    }
        
    // Convert uploaded file to base64 and save
    function uploadImage() {
        const fileInput = document.getElementById('imageUpload');
        const file = fileInput.files[0];
        const statusEl = document.getElementById('status');
            
        if (!file) {
            statusEl.innerHTML = '❌ Please select an image first';
            statusEl.className = 'status error';
            setTimeout(() => statusEl.innerHTML = '', 3000);
            return;
        }
            
        // Simple validation
        if (file.size > 5 * 1024 * 1024) {
            statusEl.innerHTML = '❌ Image too large (max 5MB)';
            statusEl.className = 'status error';
            setTimeout(() => statusEl.innerHTML = '', 3000);
            return;
        }
            
        const reader = new FileReader();
            
        reader.onload = function(e) {
            const base64Image = e.target.result;
                
            // Save to localStorage (this is your "database")
            localStorage.setItem('profilePic', base64Image);
                
            // Update the displayed image immediately
            document.getElementById('profilePic').src = base64Image;
                
            // Success feedback
            statusEl.innerHTML = '✅ Profile image updated &amp; saved!';
            statusEl.className = 'status success';
                
            console.log('%c📸 Image saved to localStorage (base64)', 'color:#00ff9d');
                
            // Clear input for next upload
            fileInput.value = '';
                
            // Auto-hide status
            setTimeout(() => {
                statusEl.innerHTML = '';
                statusEl.className = 'status';
            }, 4000);
        };
            
        reader.onerror = function() {
            statusEl.innerHTML = '❌ Failed to read image';
            statusEl.className = 'status error';
        };
            
        // Read the file as Data URL (base64)
        reader.readAsDataURL(file);
    }
        
    // Remove image and reset to default
    function removeImage() {
        const statusEl = document.getElementById('status');
            
        // Delete from localStorage
        localStorage.removeItem('profilePic');
            
        // Reset image to default
        const imgElement = document.getElementById('profilePic');
        imgElement.src = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Ccircle cx='100' cy='100' r='90' fill='%231a1a2e'/%3E%3Ccircle cx='100' cy='70' r='30' fill='%2300d4ff'/%3E%3Cpath d='M40 140 Q100 180 160 140' stroke='%2300d4ff' stroke-width='25' fill='none'/%3E%3C/svg%3E`;
            
        statusEl.innerHTML = '🗑️ Profile image removed';
        statusEl.className = 'status';
            
        console.log('%c🗑️ Image removed from localStorage', 'color:#ff3b5c');
            
        setTimeout(() => statusEl.innerHTML = '', 2500);
    }
        
    // Drag & drop support
    function enableDragAndDrop() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('imageUpload');
            
        dropZone.addEventListener('click', () => fileInput.click());
            
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#fff';
            dropZone.style.background = 'rgba(0, 212, 255, 0.2)';
        });
            
        dropZone.addEventListener('dragleave', () => {
            dropZone.style.borderColor = '#00d4ff';
            dropZone.style.background = 'rgba(0, 212, 255, 0.05)';
        });
            
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#00d4ff';
            dropZone.style.background = 'rgba(0, 212, 255, 0.05)';
                
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                // Temporarily put file into the hidden input so uploadImage() can read it
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                uploadImage();
            } else {
                const statusEl = document.getElementById('status');
                statusEl.innerHTML = '❌ Only images allowed';
                statusEl.className = 'status error';
                setTimeout(() => statusEl.innerHTML = '', 2000);
            }
        });
    }
        
     // ==================== INITIALIZE ====================
    function initialize() {
        console.log('%c🚀 Profile Image Uploader ready (HTML + JS + localStorage)', 'color:#00d4ff;font-size:18px;font-weight:600');
        loadProfilePic();
        enableDragAndDrop();
            
        // Bonus: keyboard shortcut (Ctrl/Cmd + U to open uploader)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
                e.preventDefault();
                document.getElementById('imageUpload').click();
            }
        });
    }
        
    // Start everything when page loads
    window.onload = initialize;