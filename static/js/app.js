// OPFA Community Database Search Application

class DatabaseSearchApp {
    constructor() {
        this.currentResults = [];
        this.currentKeyword = '';
        this.init();
    }

    init() {
        this.loadStats();
        this.setupEventListeners();
        this.setupTabHandling();
    }

    setupEventListeners() {
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearBtn');
        const exportBtn = document.getElementById('exportBtn');

        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });

        clearBtn.addEventListener('click', () => {
            this.clearResults();
        });

        exportBtn.addEventListener('click', () => {
            this.exportResults();
        });

        // Enter key support
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch();
            }
        });
    }

    setupTabHandling() {
        // Handle tab switching to ensure results are shown in the correct tab
        const keywordSearchTab = document.getElementById('keyword-search-tab');
        const rfpAnalysisTab = document.getElementById('rfp-analysis-tab');

        // When switching to RFP Analysis tab, hide any existing results
        rfpAnalysisTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer.style.display !== 'none') {
                resultsContainer.style.display = 'none';
            }
        });

        // When switching back to Keyword Search tab, show results if they exist
        keywordSearchTab.addEventListener('click', () => {
            const resultsContainer = document.getElementById('resultsContainer');
            if (this.currentResults.length > 0 && resultsContainer.style.display === 'none') {
                resultsContainer.style.display = 'block';
            }
        });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            if (stats.error) {
                console.error('Error loading stats:', stats.error);
                return;
            }

            const statsDisplay = document.getElementById('stats-display');
            statsDisplay.innerHTML = `
                <div>${stats.total_records} Total Records</div>
                <div>${stats.records_with_linkedins} With LinkedIn</div>
                <div>${stats.records_with_resumes} With Resumes</div>
            `;
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        const keyword = searchInput.value.trim();

        if (!keyword) {
            this.showError('Please enter a keyword or phrase to search for');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keyword })
            });

            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.currentResults = data.results;
            this.currentKeyword = data.keyword;
            this.displayResults(data);

        } catch (error) {
            this.showError('An error occurred while searching. Please try again.');
            console.error('Search error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(data) {
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsTitle = document.getElementById('resultsTitle');
        const resultsList = document.getElementById('resultsList');

        // Update title
        const count = data.count;
        const keyword = data.keyword;
        resultsTitle.innerHTML = `
            <i class="fas fa-search me-2"></i>
            Found ${count} result${count !== 1 ? 's' : ''} for "${keyword}"
        `;

        // Clear previous results
        resultsList.innerHTML = '';

        if (count === 0) {
            resultsList.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle me-2"></i>
                        No results found for "${keyword}". Try a different keyword or phrase.
                    </div>
                </div>
            `;
        } else {
            // Display results in cards
            data.results.forEach((result, index) => {
                const card = this.createResultCard(result, keyword);
                resultsList.appendChild(card);
            });
        }

        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    createResultCard(result, keyword) {
        const template = document.getElementById('resultCardTemplate');
        const card = template.content.cloneNode(true);

        // Set person name
        const personName = card.querySelector('.person-name');
        const firstName = result.first_name || '';
        const lastName = result.last_name || '';
        const fullName = `${firstName} ${lastName}`.trim() || 'Unknown Name';
        personName.textContent = this.highlightKeyword(fullName, keyword);

        // Set location
        const location = card.querySelector('.location');
        const city = result.city || '';
        const country = result.country || '';
        const locationText = [city, country].filter(Boolean).join(', ') || 'Location not specified';
        location.textContent = locationText;

        // Add fields to card body
        const fieldsContainer = card.querySelector('.result-fields');
        this.addFieldsToCard(fieldsContainer, result, keyword);

        return card;
    }

    addFieldsToCard(container, result, keyword) {
        const fieldMappings = {
            'email': { label: 'Email', icon: 'fas fa-envelope', type: 'email' },
            'email_other': { label: 'Other Email', icon: 'fas fa-envelope', type: 'email' },
            'linkedin': { label: 'LinkedIn', icon: 'fab fa-linkedin', type: 'link' },
            'current_job': { label: 'Current Job', icon: 'fas fa-briefcase' },
            'current_company': { label: 'Current Company', icon: 'fas fa-building' },
            'linkedin_summary': { label: 'LinkedIn Summary', icon: 'fas fa-file-alt' },
            'resume': { label: 'Resume', icon: 'fas fa-file-pdf', type: 'text' },
            'years_xp': { label: 'Years Experience', icon: 'fas fa-clock' },
            'years_sustainability_xp': { label: 'Sustainability Experience', icon: 'fas fa-leaf' },
            'linkedin_skills': { label: 'LinkedIn Skills', icon: 'fas fa-tools' },
            'key_competencies': { label: 'Key Competencies', icon: 'fas fa-star' },
            'key_sectors': { label: 'Key Sectors', icon: 'fas fa-industry' },
            'executive_summary': { label: 'Executive Summary', icon: 'fas fa-user-tie' },
            'gender_identity': { label: 'Gender Identity', icon: 'fas fa-user' },
            'race_ethnicity': { label: 'Race/Ethnicity', icon: 'fas fa-users' },
            'lgbtqia': { label: 'LGBTQIA+', icon: 'fas fa-heart' },
            'source': { label: 'Source', icon: 'fas fa-info-circle' }
        };

        // Add fields in order
        Object.entries(fieldMappings).forEach(([fieldName, config]) => {
            const value = result[fieldName];
            if (value && value.trim()) {
                const fieldGroup = this.createFieldGroup(config.label, value, config.icon, config.type, keyword);
                container.appendChild(fieldGroup);
            }
        });
    }

    createFieldGroup(label, value, icon, type = 'text', keyword = '') {
        const fieldGroup = document.createElement('div');
        fieldGroup.className = 'field-group';

        const fieldLabel = document.createElement('div');
        fieldLabel.className = 'field-label';
        fieldLabel.innerHTML = `<i class="${icon} field-icon"></i>${label}`;

        const fieldValue = document.createElement('div');
        fieldValue.className = 'field-value';

        if (type === 'email') {
            fieldValue.innerHTML = `<a href="mailto:${value}" target="_blank">${this.highlightKeyword(value, keyword)}</a>`;
        } else if (type === 'link') {
            fieldValue.innerHTML = `<a href="${value}" target="_blank">${this.highlightKeyword(value, keyword)}</a>`;
        } else if (label.toLowerCase().includes('resume')) {
            // Handle resume as expandable toggle
            const resumeId = 'resume-' + Math.random().toString(36).substr(2, 9);
            fieldValue.innerHTML = `
                <div class="resume-toggle">
                    <button class="btn btn-sm btn-outline-secondary" onclick="toggleResume('${resumeId}')">
                        <i class="fas fa-eye me-1"></i>View Resume
                    </button>
                    <div id="${resumeId}" class="resume-content" style="display: none; margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <div>
                            ${this.highlightKeyword(value, keyword)}
                        </div>
                    </div>
                </div>
            `;
        } else if (label.toLowerCase().includes('skills') || label.toLowerCase().includes('competencies') || label.toLowerCase().includes('sectors')) {
            // Handle skills/competencies as tags
            const skills = value.split(',').map(skill => skill.trim()).filter(Boolean);
            const skillsHtml = skills.map(skill => 
                `<span class="skill-tag">${this.highlightKeyword(skill, keyword)}</span>`
            ).join('');
            fieldValue.innerHTML = `<div class="skills-tags">${skillsHtml}</div>`;
        } else {
            fieldValue.innerHTML = this.highlightKeyword(value, keyword);
        }

        fieldGroup.appendChild(fieldLabel);
        fieldGroup.appendChild(fieldValue);

        return fieldGroup;
    }

    highlightKeyword(text, keywords) {
        if (!keywords || !text) return text;
        
        // Split keywords by comma and clean them
        const keywordList = keywords.split(',').map(kw => kw.trim()).filter(kw => kw);
        
        if (keywordList.length === 0) return text;
        
        let highlightedText = text;
        
        // Highlight each keyword with a different color
        keywordList.forEach((keyword, index) => {
            const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            const colorClass = index === 0 ? 'highlight' : `highlight-${index + 1}`;
            highlightedText = highlightedText.replace(regex, `<span class="${colorClass}">$1</span>`);
        });
        
        return highlightedText;
    }

    clearResults() {
        const resultsContainer = document.getElementById('resultsContainer');
        const searchInput = document.getElementById('searchInput');
        
        resultsContainer.style.display = 'none';
        searchInput.value = '';
        this.currentResults = [];
        this.currentKeyword = '';
        
        searchInput.focus();
    }

    exportResults() {
        if (!this.currentResults.length) {
            this.showError('No results to export');
            return;
        }

        // Create CSV content
        const headers = Object.keys(this.currentResults[0]);
        const csvContent = [
            headers.join(','),
            ...this.currentResults.map(result => 
                headers.map(header => {
                    const value = result[header] || '';
                    // Escape commas and quotes in CSV
                    return `"${value.replace(/"/g, '""')}"`;
                }).join(',')
            )
        ].join('\n');

        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `opfa_search_results_${this.currentKeyword}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const searchBtn = document.querySelector('#searchForm button[type="submit"]');
        
        if (show) {
            loadingSpinner.style.display = 'block';
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
        } else {
            loadingSpinner.style.display = 'none';
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Search';
        }
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth' });
    }

    hideError() {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.style.display = 'none';
    }
}

// Global function for toggling resume content
function toggleResume(resumeId) {
    const resumeContent = document.getElementById(resumeId);
    const button = resumeContent.previousElementSibling;
    const icon = button.querySelector('i');
    
    if (resumeContent.style.display === 'none') {
        resumeContent.style.display = 'block';
        icon.className = 'fas fa-eye-slash me-1';
        button.innerHTML = '<i class="fas fa-eye-slash me-1"></i>Hide Resume';
    } else {
        resumeContent.style.display = 'none';
        icon.className = 'fas fa-eye me-1';
        button.innerHTML = '<i class="fas fa-eye me-1"></i>View Resume';
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DatabaseSearchApp();
}); 