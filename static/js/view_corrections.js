document.addEventListener('DOMContentLoaded', () => {
    const originalTexts = document.querySelectorAll('.original-text');
    originalTexts.forEach((text) => {
        text.addEventListener('click', (event) => {
            const correctionId = event.target.getAttribute('data-id');
            const dropdown = document.getElementById(`details-${correctionId}`);
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        }); 
    });

    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            const tabId = event.target.getAttribute('data-tab');
            const correctionRow = event.target.closest('.correction-row');

            correctionRow.querySelectorAll('.tab-content').forEach((content) => {
                content.classList.remove('active');
            });

            document.getElementById(tabId).classList.add('active');

            correctionRow.querySelectorAll('.tab-button').forEach((btn) => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
        });
    });
}); 