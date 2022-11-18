function toggleTheme() {
    let theme = document.documentElement.getAttribute('data-theme');
    if (theme == "dark") {
        theme = "light";

    } else {
        theme = "dark";
    }
    sessionStorage.setItem('data-theme', theme);

    document.documentElement.classList.add('color-theme-in-transition')
    document.documentElement.setAttribute('data-theme', theme)
    window.setTimeout(function () {
        document.documentElement.classList.remove('color-theme-in-transition')
    }, 300)

}

function toggleDyslexia() {
    let hasToggle = document.documentElement.hasAttribute('data-dyslexia-mode');
    let toggle = document.documentElement.getAttribute('data-dyslexia-mode');
    if (toggle == "true") {
        toggle = "false";

    } else {
        toggle = "true";
    }
    sessionStorage.setItem('data-dyslexia-mode', toggle);
    document.documentElement.setAttribute('data-dyslexia-mode', toggle);
}
window.onload = (event) => {

    let theme = document.documentElement.getAttribute('data-theme');
    let sessionTheme = sessionStorage.getItem('data-theme');
    if (sessionTheme != theme) {
        document.documentElement.setAttribute('data-theme', sessionTheme);
    }
    let dyslexia_toggle = document.documentElement.getAttribute('data-dyslexia-mode');
    let sessionDyslexiaToggle = sessionStorage.getItem('data-dyslexia-mode');
    if (sessionDyslexiaToggle != dyslexia_toggle) {
        document.documentElement.setAttribute('data-dyslexia-mode', sessionDyslexiaToggle);
    }
}