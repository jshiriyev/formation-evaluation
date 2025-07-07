import numpy as np

def eigencall(stat,Nr,Nb,B1,B2):
    
    Cmat = np.zeros((2*Nb,2*Nb,Nr));

    Lambda = np.zeros((2*Nb,Nr));

    for l in range(Nr):

        A1e = integral(-1./stat.qe(:,l),stat.qe(:,l),stat.qe(:,l),3);
        A1h = integral(-1./stat.qh(:,l),stat.qh(:,l),stat.qh(:,l),3);

        A2e = integral(stat.k2e(:,l)./stat.pe(:,l),stat.qe(:,l),stat.qe(:,l),1);
        A2h = integral(stat.k2h(:,l)./stat.ph(:,l),stat.qh(:,l),stat.qh(:,l),1);

        Be = integral(1./stat.pe(:,l),stat.qe(:,l),stat.qe(:,l),1);
        Bh = integral(1./stat.ph(:,l),stat.qh(:,l),stat.qh(:,l),1);

        Ae = A1e+A2e;
        Ah = A1h+A2h;

        [CCe,DDe] = eig(Ae,Be,'vector');
        [CCh,DDh] = eig(Ah,Bh,'vector');

        Cmat(B1,B1,l) = orthog(CCe,Be,Nb);
        Cmat(B2,B2,l) = orthog(CCh,Bh,Nb);

        Lambda(B1,l) = sqrt(DDe);
        Lambda(B2,l) = sqrt(DDh);
    
    return Cmat, Lambda

def orthog(Ceta_old,Beta,Nb):
    
    #  Correction for orthogonality relationship
    
    Ceta = Ceta_old;
    
    noneI = transpose(Ceta_old)*Beta*Ceta_old;
    noneI = sqrt(1./diag(noneI));
    
    for i in range(Nb)
        Ceta(:,i) = Ceta_old(:,i)*noneI(i);
    
    return Ceta