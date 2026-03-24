using UnityEngine;
using UnityEngine.SceneManagement;

public class BootstrapLoader : MonoBehaviour
{
    [SerializeField] private string gameplaySceneName = "Gameplay";

    private void Start()
    {
        if (string.IsNullOrWhiteSpace(gameplaySceneName))
        {
            return;
        }

        Scene activeScene = SceneManager.GetActiveScene();
        if (activeScene.name == gameplaySceneName)
        {
            return;
        }

        SceneManager.LoadScene(gameplaySceneName, LoadSceneMode.Single);
    }
}
