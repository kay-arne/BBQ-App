document.addEventListener('DOMContentLoaded', () => {
    // Selecteer belangrijke DOM-elementen
    const form = document.getElementById('bbqForm');
    const personsAdultsInput = document.getElementById('personsAdults');
    const personsChildrenInput = document.getElementById('personsChildren'); // Niet direct voor bedrag, wel voor logica
    const houseNumberInput = document.getElementById('houseNumber'); // Voor validatie
    const totalAmountSpan = document.getElementById('totalAmount');
    const messageDiv = document.getElementById('message');
    const submitButton = form.querySelector('button[type="submit"]');
    const spinner = submitButton.querySelector('.spinner');

    // De 'pricePerAdult' variabele wordt vanuit index.html via Jinja doorgegeven.
    // Zorg dat deze beschikbaar is (bijv. in een <script> tag net voor het sluiten van de <body> in index.html).
    // Voorbeeld: <script>const pricePerAdult = {{ bbq_details.price_per_adult }};</script>

    /**
     * Berekent en update het totaalbedrag op basis van het aantal volwassenen.
     * Kinderen zijn gratis en beïnvloeden het bedrag niet.
     */
    function updateTotalPrice() {
        const adults = parseInt(personsAdultsInput.value) || 0; // Gebruik 0 als de input leeg is

        // Controleer of pricePerAdult gedefinieerd is
        if (typeof pricePerAdult === 'undefined') {
            console.error("Fout: 'pricePerAdult' is niet gedefinieerd. Zorg dat het wordt doorgegeven vanuit de HTML.");
            return;
        }

        const total = adults * pricePerAdult;
        totalAmountSpan.textContent = `€${total.toFixed(2)}`;
    }

    // Luister naar wijzigingen in het aantal volwassenen en kinderen om het totaalbedrag bij te werken
    if (personsAdultsInput) {
        personsAdultsInput.addEventListener('input', updateTotalPrice);
    }
    if (personsChildrenInput) {
        // Hoewel kinderen de prijs niet beïnvloeden, kan het handig zijn om de totalen bij te werken als deze ook worden getoond
        personsChildrenInput.addEventListener('input', updateTotalPrice); 
    }

    // Roep updateTotalPrice direct aan bij het laden van de pagina om het initiële bedrag te tonen
    updateTotalPrice();

    /**
     * Handelt het indienen van het formulier af, inclusief validatie,
     * laadindicator en het verzenden van gegevens naar de backend.
     */
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Voorkom de standaard browser indiening

        // Toon de laadindicator en maak de knop onklikbaar
        submitButton.disabled = true;
        // Wijzig de tekst van de knop
        const buttonText = submitButton.querySelector('span:first-child');
        buttonText.textContent = 'Verwerken...'; 
        spinner.style.display = 'inline-block'; // Maak de spinner zichtbaar

        // Verberg eerdere berichten
        messageDiv.style.display = 'none';
        messageDiv.className = ''; // Reset CSS-klassen

        // Haal de data op uit het formulier
        const name = document.getElementById('name').value.trim(); // .trim() verwijdert witruimte aan begin/eind
        const houseNumber = houseNumberInput.value.trim();
        const email = document.getElementById('email').value.trim();
        const personsAdults = parseInt(personsAdultsInput.value) || 0;
        const personsChildren = parseInt(personsChildrenInput.value) || 0;
        const allergiesNotes = document.getElementById('allergiesNotes').value.trim();
        
        // Bereken het totaalbedrag opnieuw (voor zekerheid)
        const totalAmount = (personsAdults * pricePerAdult).toFixed(2); // .toFixed(2) voor 2 decimalen

        // Client-side validatie
        if (!name || !houseNumber || personsAdults < 1) { // Naam, huisnummer en minstens 1 volwassene zijn verplicht
            messageDiv.textContent = 'Vul alstublieft uw naam, huisnummer en ten minste 1 volwassene in.';
            messageDiv.classList.add('error');
            messageDiv.style.display = 'block';
            
            // Verberg spinner en maak knop weer klikbaar bij validatiefout
            submitButton.disabled = false;
            buttonText.textContent = '🚀 Aanmelden en Betalen';
            spinner.style.display = 'none';
            return;
        }

        // Reguliere expressie validatie voor huisnummer
        const houseNumberRegex = /^\d+[a-zA-Z]?$/;
        if (!houseNumberRegex.test(houseNumber)) {
            messageDiv.textContent = 'Ongeldig huisnummer. Voer enkel cijfers en optioneel één letter (bijv. 46 of 46a) in.';
            messageDiv.classList.add('error');
            messageDiv.style.display = 'block';

            // Verberg spinner en maak knop weer klikbaar bij validatiefout
            submitButton.disabled = false;
            buttonText.textContent = '🚀 Aanmelden en Betalen';
            spinner.style.display = 'none';
            return;
        }

        try {
            // Verzend de gegevens naar de backend
            const response = await fetch('/api/register', { // Endpoint op de Flask server
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    name, 
                    houseNumber, 
                    email, 
                    personsAdults, 
                    personsChildren,
                    allergiesNotes,
                    totalAmount
                })
            });

            const result = await response.json(); // Lees de JSON-respons van de server

            if (response.ok) { // Controleer of de HTTP-status 2xx is
                messageDiv.textContent = result.message;
                messageDiv.classList.add('success');
                messageDiv.style.display = 'block';
                form.reset(); // Reset het formulier na succesvolle indiening
                updateTotalPrice(); // Werk het totaalbedrag bij na reset (zet terug naar initiële staat)

                // Stuur de gebruiker door naar de Bunq.me betaallink na een korte vertraging
                setTimeout(() => {
                    if (result.paymentUrl) {
                        window.location.href = result.paymentUrl;
                    } else {
                        // Als er om een of andere reden geen betaal-URL is, blijf op de pagina
                        alert('Aanmelding succesvol, maar er is geen betaallink ontvangen.');
                    }
                }, 1500); 
            } else {
                // Toon foutmelding van de server
                messageDiv.textContent = result.message || 'Er is een onbekende fout opgetreden.';
                messageDiv.classList.add('error');
                messageDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Fout bij verzenden formulier:', error);
            messageDiv.textContent = 'Er is een netwerkfout opgetreden of de server is niet bereikbaar.';
            messageDiv.classList.add('error');
            messageDiv.style.display = 'block';
        } finally {
            // Herstel de knop en verberg de spinner, ongeacht het resultaat
            submitButton.disabled = false;
            buttonText.textContent = '🚀 Aanmelden en Betalen';
            spinner.style.display = 'none';
        }
    });
});