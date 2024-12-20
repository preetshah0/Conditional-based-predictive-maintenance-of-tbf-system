using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using UnityEngine.Networking;
using System.Collections.Generic; // Include for generic Queue

public class UpdateInputFields : MonoBehaviour
{
    public InputField InputFieldTEMP;   // Reference to TEMP input field
    public InputField InputFieldHUM;    // Reference to HUM input field
    public InputField InputFieldVIB;    // Reference to VIB input field
    public InputField InputFieldVOLT;   // Reference to VOLTAGE input field
    public InputField InputFieldCUR;    // Reference to CUR input field
    public InputField InputFieldMQ135;  // Reference to MQ135 input field

    private string apiEndpoint = "http://127.0.0.1:5000/get_data"; // Backend API endpoint

    // Queue to store incoming data (generic Queue<string>)
    private Queue<string> dataQueue = new Queue<string>();

    private void Start()
    {
        // Start the coroutine to fetch data continuously
        StartCoroutine(FetchDataCoroutine());
    }

    // Coroutine to fetch data from the server
    IEnumerator FetchDataCoroutine()
    {
        while (true)
        {
            using (UnityWebRequest webRequest = UnityWebRequest.Get(apiEndpoint))
            {
                yield return webRequest.SendWebRequest();

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    string responseData = webRequest.downloadHandler.text;

                    // Add the received data to the queue
                    lock (dataQueue)
                    {
                        dataQueue.Enqueue(responseData);
                    }

                    // Automatically update the input fields if new data is available
                    UpdateInputFieldsFromQueue();
                }
                else
                {
                    Debug.LogError("Error Fetching Data: " + webRequest.error);
                }
            }

            // Optionally adjust the delay between requests
            yield return new WaitForSeconds(0.5f); // Adjust frequency as needed
        }
    }

    // Method to update input fields from the latest data in the queue
    private void UpdateInputFieldsFromQueue()
    {
        lock (dataQueue)
        {
            if (dataQueue.Count > 0)
            {
                // Get the latest data from the queue
                string latestData = dataQueue.Dequeue();
                Debug.Log("Processing Data: " + latestData);

                try
                {
                    // Parse the JSON data
                    var parsedData = JsonUtility.FromJson<SensorData>(latestData);

                    // Update the input fields with the parsed data
                    InputFieldTEMP.text = parsedData.TEMP.ToString("F2");
                    InputFieldHUM.text = parsedData.HUM.ToString("F2");
                    InputFieldVIB.text = parsedData.VIB.ToString("F2");
                    InputFieldVOLT.text = parsedData.VOLTAGE.ToString("F2"); // Use VOLTAGE
                    InputFieldCUR.text = parsedData.CUR.ToString("F2");
                    InputFieldMQ135.text = parsedData.MQ135.ToString("F2");  // Display MQ135 data
                }
                catch (System.Exception e)
                {
                    Debug.LogError("Error Parsing Data: " + e.Message);
                }
            }
            else
            {
                Debug.LogWarning("No data in queue to process.");
            }
        }
    }
}

// Class to represent the sensor data structure
[System.Serializable]
public class SensorData
{
    public float TEMP;    // Temperature
    public float HUM;     // Humidity
    public float VIB;     // Vibration
    public float VOLTAGE; // Voltage
    public float CUR;     // Current
    public float MQ135;   // MQ135 (Air Quality)
}
