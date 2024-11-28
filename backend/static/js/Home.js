const handleDownload = async (song, format = 'mp3') => {
    try {
        const response = await axios.get(
            `/api/songs/stream/${song._id}?format=${format}`,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                responseType: 'blob'
            }
        );

        // Create a URL for the blob
        const url = window.URL.createObjectURL(new Blob([response.data]));
        
        // Create a temporary link element
        const link = document.createElement('a');
        link.href = url;
        
        // Set the download filename
        const extension = format.toLowerCase();
        link.setAttribute('download', `${song.title}.${extension}`);
        
        // Append to the document, click it, and remove it
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        
        // Clean up the URL
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading song:', error);
        setError('Failed to download song');
    }
}; 