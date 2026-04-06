const hoverEye = document.getElementById('hoverEye');
const passwordInput = document.getElementById('contrasena');
hoverEye.addEventListener('mouseenter', () => {
  passwordInput.setAttribute('type', 'text'); // show password
});
hoverEye.addEventListener('mouseleave', () => {
  passwordInput.setAttribute('type', 'password'); // hide password
});


function base64urlToUint8Array(base64urlString) {
  const padding = "=".repeat((4 - (base64urlString.length % 4)) % 4);
  const base64 = base64urlString.replace(/-/g, "+").replace(/_/g, "/") + padding;
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function loginWithPasskey() {
  //const correo = document.querySelector("#correo_electronico").value.trim();
  //if (!correo) {
  //  alert("Por favor ingresa tu correo electrónico antes de usar Passkey.");
  //  return;
  //}
  try {
    // 1️⃣ Request challenge from backend
    const resp = await fetch("/authentication/passkey/login/options", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      //body: JSON.stringify({ correo_electronico: correo })
    });
    if (!resp.ok) throw new Error("Usuario sin passkey registrado.");
    const options = await resp.json();

options.challenge = base64urlToUint8Array(options.challenge);
options.allowCredentials = (options.allowCredentials || []).map(cred => ({
  ...cred,
  id: base64urlToUint8Array(cred.id),
}));

const assertion = await navigator.credentials.get({ publicKey: options });

    // Convert binary buffers to base64 strings for transport
    const credential = {
      id: assertion.id,
      raw_id: btoa(String.fromCharCode(...new Uint8Array(assertion.rawId))),
      type: assertion.type,
      response: {
        authenticator_data: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
        client_data_json: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
        signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
        user_handle: assertion.response.userHandle
          ? btoa(String.fromCharCode(...new Uint8Array(assertion.response.userHandle)))
          : null,
      }
    };

    // 3️⃣ Verify with backend
    const verifyResp = await fetch("/authentication/passkey/login/verify", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(credential)
    });
	console.log(verifyResp)
    if (verifyResp.ok) {
      window.location.href = "/"; // Redirect on success
    } else {
      alert("No se pudo verificar el Passkey. Inténtalo nuevamente.");
    }
  } catch (err) {
    console.error(err);
    alert("Error al usar Passkey: " + err.message);
  }
}
  document.getElementById("onetimecodeLoginBtn").addEventListener("click", () => {
    const email = document.getElementById("correo_electronico").value.trim();
    if (!email) {
      alert("Por favor, ingresa tu correo electrónico.");
      return;
    }
    const encodedEmail = encodeURIComponent(email);
    window.location.href = `/authentication/one_time_code_login/${encodedEmail}`;
  });
// Attach to button
document.getElementById("passkeyLoginBtn").addEventListener("click", loginWithPasskey);
