// File Upload Handling
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.querySelector('#file-input');
    
    if (uploadArea) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;
                handleFileUpload(files[0]);
            }
        });
    }
});

// Handle File Upload
function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading state
    const uploadArea = document.querySelector('.upload-area');
    uploadArea.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        displayDeviceInfo(data);
    })
    .catch(error => {
        console.error('Error:', error);
        uploadArea.innerHTML = '<p class="text-danger">Error uploading file. Please try again.</p>';
    });
}

// Display Device Information
function displayDeviceInfo(data) {
    const deviceInfo = document.querySelector('.device-info');
    if (!deviceInfo) return;
    
    deviceInfo.innerHTML = `
        <h4>${data.device_name}</h4>
        <p>${data.description}</p>
        <div class="mt-3">
            <h5>Material Composition</h5>
            <div class="material-chart">
                ${data.material_chart}
            </div>
        </div>
        <div class="mt-3">
            <h5>Recycling Value</h5>
            <p>${data.recycling_value}</p>
        </div>
    `;
    
    // Add fade-in animation
    deviceInfo.classList.add('fade-in');
}

// Reward Redemption
function redeemReward(rewardName, points) {
    fetch('/redeem_reward', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            reward_name: rewardName,
            points: points
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Reward redeemed successfully!');
            location.reload();
        } else {
            alert(data.message || 'Error redeeming reward. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error redeeming reward. Please try again.');
    });
}

// Newsletter Subscription
const newsletterForm = document.querySelector('.newsletter form');
if (newsletterForm) {
    newsletterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const email = this.querySelector('input[type="email"]').value;
        
        // Here you would typically send this to your backend
        alert('Thank you for subscribing!');
        this.reset();
    });
}

// Smooth Scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
}); 