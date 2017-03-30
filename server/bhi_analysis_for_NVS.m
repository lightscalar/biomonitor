function bhi_analysis()

	%%%	Method and algorithm desgined by Sardar Ansari, PhD, January 2016
	%%% Code written by Sardar Ansari, PhD, January 2016, revised March 2017
	%%% Please do not publish or distribute

    interp_len = 500;	% interpolate the beats to 'interp_len' before analysis
    sample_every = 60;	% analyze beats every 'sample_every' seconds

    addpath(genpath('.\'));
    
    subjects = {'051016B+';
    '041916B+';
    '051216A+';
    '041715A-';
    '042115B-';
    '070215A-';
    '071415A+';
    '072315D-';
    '080315A+';
    '080315B-';
    '081215A-';
    '081915A-';
    'PZT111716B-';
    'PZT112916B-';
    'PZT121316A+'};

    nn_data = cell(length(subjects),1);
    for si = 1:length(subjects)
        tc = tic;

	% load the signal, the beat locations, the labels, etc.
        [labels, idh_labels, pzt_usable_cln, pzt_usable_pks, samples, ~, start, Fs] = 
	feval(['bhi_analysis_', subjects{si}(1:end-1)]);	

         % find the index of the first beat after the beginning of the dialysis  
        last_i = 0;
        first_i = find(samples(pzt_usable_pks)>start,1,'first');	
	% if 'sample_every' has passed from the last beat that was analyzed and there is not a large gap between this beat and the previous one	
        for i = first_i:length(pzt_usable_pks)
            if(i == first_i || (samples(pzt_usable_pks(i)) > samples(pzt_usable_pks(last_i)) +
		    sample_every*Fs && samples(pzt_usable_pks(i+1))-samples(pzt_usable_pks(i)) < 3*Fs))
			
				period = interp1(linspace(0,1,pzt_usable_pks(i+1)-pzt_usable_pks(i)), pzt_usable_cln(pzt_usable_pks(i):pzt_usable_pks(i+1)-1), linspace(0,1,interp_len)); % interpolate the beat to have 'interp_len' samples

				[b,c]=l1trend2(period,range(period)/20);	
				% find the outline of the signal using
				% taut-string approximation (b). Use an epsilon
				% equal to 5% of the amplitude of the signal.
				
				gauss_feats = gauss_feat_ext(period-b);		% remove the outline of the signal to amplify the reflection waves. Then, quanitify the waves using a combination of Gaussian functions.

				nn_data{si} = [nn_data{si} ; si, i, gauss_feats, idh_labels(i), labels(i)];		% store the features (mean, std and amplitude of the Gaussians) along with the labels, etc.				
                
                last_i = i;
            end
        end 
        toc(tc);
    end
    
    nn_data = cell2mat(nn_data);
    
    save('nn_data_15_subj','nn_data');
    
    rmpath(genpath('.\'));
end

function feats = gauss_feat_ext(sig)

	% this function gets a PVDF beats and models it using five Gaussian functions and returns their means, stds and amplitudes.

    sig = interp1(linspace(0,1,length(sig)), sig, linspace(0,1,700));	% interpolate the beat to have 700 points
    sig = sig-min(sig);		% normalize the beat between zero and one
    sig = sig/max(sig);
    
    [xData, yData] = prepareCurveData([], sig);		% prepare the data for curve fitting
    
    ft = fittype('gauss8');		% use eight equally-spaced Gaussians to find initial fits
    opts = fitoptions('Method', 'NonlinearLeastSquares');
    opts.Display = 'Off';
    opts.Lower = zeros(1,3*8);	% define the upper and lower bounds for amplitude, location and std of the Gaussians
    opts.Upper = [2 700 350 2 700 350 2 700 350 2 700 350 2 700 350 2 700 350 2 700 350 2 700 350];
    opts.StartPoint = zeros(1,3*8);
    opts.StartPoint(1:3:end) = max(sig)/2;
    opts.StartPoint(2:3:end) = 0:100:700;	% equaly space them between 0 and 700.
    opts.StartPoint(3:3:end) = 5;
    
    fitresult = fit( xData, yData, ft, opts );	% find the initial fit
        
    coeffs = coeffvalues(fitresult);
    as = coeffs(1:3:end);
    bs = coeffs(2:3:end);
    cs = coeffs(3:3:end);
    
    while(sum(bs(2:end)-bs(1:end-1) < 75)>0 & length(as)>5)	% combine Gaussians that are closer than 75 points to each other until there are only five Gaussians left
        b_diffs = bs(2:end)-bs(1:end-1);
        ix = find(b_diffs<75,1,'first');
        as(ix) = mean([as(ix),as(ix+1)]);
        as(ix+1) = [];
        bs(ix) = mean([bs(ix),bs(ix+1)]);
        bs(ix+1) = [];
        cs(ix) = mean([cs(ix),cs(ix+1)]);
        cs(ix+1) = [];
    end
    
    while(length(as)>5)	% if there are more than five Gaussians left, start removing the ones with the lowest amplitudes
        [~,ix] = min(as);
        as(ix) = [];
        bs(ix) = [];
        cs(ix) = [];
    end
	
    ft = fittype('gauss5');		% define a new fit with five Gaussians
    opts = fitoptions('Method', 'NonlinearLeastSquares');
    opts.Display = 'Off';
    opts.Lower = zeros(1,3*5);
    opts.Upper = [2 700 350 2 700 350 2 700 350 2 700 350 2 700 350];	
    
    opts.StartPoint = zeros(1,3*5);		% use the parameters from the remaining five Gaussians from the initial fit to initialize the new fit
    opts.StartPoint(1:3:end) = as;
    opts.StartPoint(2:3:end) = bs;
    opts.StartPoint(3:3:end) = cs;    

    fitresult = fit( xData, yData, ft, opts );	% find the best fit
    
    feats = coeffvalues(fitresult);		% return the parameters

end
