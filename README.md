```mermaid
sequenceDiagram
    participant U as User
    participant E as Entropy Platform
    participant M as AI Model
    participant P as Proof Generator

    U->>E: Sign in
    E-->>U: Authentication confirmation

    alt Upload Model
        U->>E: Upload trained AI model
        E->>E: Store and make model visible to others
    end

    U->>E: Subscribe to an AI model
    U->>E: Request inference for a specific token
    E->>M: Run inference
    M->>P: Generate cryptographic proof during inference
    M-->>E: Return predicted values and trade positions
    P-->>E: Return cryptographic proof
    E->>U: Provide inference results and cryptographic proof
    U->>U: Verify proof independently

    alt Rate Model
        U->>E: Upvote or downvote model based on performance
        E->>E: Update model rating
    end
